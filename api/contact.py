"""Contact form: send one message to comms@dogwoof.ai.

A Vercel Python function. The form on /contact posts here. Each message is
sent as an email from the comms@dogwoof.ai Google Workspace account to the
same inbox, with Reply-To set to the visitor. Nothing is stored or logged.

Environment (set in Vercel, never in git):
    SMTP_USER       the Workspace account, e.g. comms@dogwoof.ai
    SMTP_PASSWORD   an app password for that account
    CONTACT_TO      optional, defaults to comms@dogwoof.ai

Without SMTP_PASSWORD the function answers 503 and the page asks visitors to
email directly.
"""
import json
import os
import re
import smtplib
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

INBOX = "comms@dogwoof.ai"
LIMITS = {"name": 200, "email": 254, "message": 5000}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_BODY = 20_000


def clean(form):
    """Return (fields, error). fields has name, email and message."""
    if form.get("website", "").strip():
        return None, "spam"
    fields = {k: form.get(k, "").strip() for k in LIMITS}
    # Header values must stay on one line.
    for k in ("name", "email"):
        fields[k] = " ".join(fields[k].split())
    if not fields["email"] or not fields["message"]:
        return None, "Please add your email and a message."
    if not EMAIL.match(fields["email"]):
        return None, "Please check your email address."
    for k, limit in LIMITS.items():
        if len(fields[k]) > limit:
            return None, f"Please keep your {k} under {limit} characters."
    return fields, None


def build(fields, sender, to):
    msg = EmailMessage()
    who = fields["name"] or fields["email"]
    msg["Subject"] = f"Website message from {who}"
    msg["From"] = f"DogwoofAI website <{sender}>"
    msg["To"] = to
    msg["Reply-To"] = fields["email"]
    msg.set_content(
        f"Name: {fields['name'] or '(not given)'}\n"
        f"Email: {fields['email']}\n\n"
        f"{fields['message']}\n"
    )
    return msg


def send(msg, user, password):
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)


def parse(body, content_type):
    if content_type.startswith("application/json"):
        data = json.loads(body or b"{}")
        return {k: str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    return {k: v[0] for k, v in parse_qs(body.decode("utf-8", "replace")).items()}


def handle(body, content_type, env=None, sender=None):
    """Return (status, result) where result is "sent", "spam" or an error."""
    env = os.environ if env is None else env
    sender = sender or send
    try:
        form = parse(body, content_type)
    except ValueError:
        return 400, "Please try again."
    fields, error = clean(form)
    if error == "spam":
        return 200, "sent"  # Look normal to bots, send nothing.
    if error:
        return 400, error
    password = env.get("SMTP_PASSWORD")
    if not password:
        return 503, f"The form is not switched on yet. Please email {INBOX}."
    user = env.get("SMTP_USER", INBOX)
    try:
        sender(build(fields, user, env.get("CONTACT_TO", INBOX)), user, password)
    except (smtplib.SMTPException, OSError):
        return 502, f"Your message could not be sent. Please email {INBOX}."
    return 200, "sent"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            status, result = 413, "Your message is too long."
        else:
            body = self.rfile.read(length)
            status, result = handle(body, self.headers.get("Content-Type", ""))
        if "application/json" in self.headers.get("Accept", ""):
            payload = {"ok": True} if result == "sent" else {"ok": False, "error": result}
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        # A plain form post, without JavaScript: go back to the page.
        self.send_response(303)
        self.send_header("Location", "/contact?sent=1#form" if result == "sent" else "/contact?error=1#form")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        self.send_response(303)
        self.send_header("Location", "/contact")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass  # Never log messages or addresses.
