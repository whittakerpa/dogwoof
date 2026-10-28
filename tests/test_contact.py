"""Tests for the contact form function. Run: python3 -m unittest discover tests"""
import http.client
import json
import pathlib
import sys
import threading
import unittest
from http.server import HTTPServer
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "api"))
import contact  # noqa: E402

ENV = {"SMTP_USER": "comms@dogwoof.ai", "SMTP_PASSWORD": "test"}
FORM = b"name=Ada+Lovelace&email=ada%40example.com&message=Hello+there&website="


class Handle(unittest.TestCase):
    def test_sends_to_inbox_with_reply_to(self):
        sent = []
        status, result = contact.handle(FORM, "application/x-www-form-urlencoded", ENV,
                                        lambda m, u, p: sent.append(m))
        self.assertEqual((status, result), (200, "sent"))
        msg = sent[0]
        self.assertEqual(msg["To"], "comms@dogwoof.ai")
        self.assertEqual(msg["Reply-To"], "ada@example.com")
        self.assertIn("comms@dogwoof.ai", msg["From"])
        self.assertIn("Hello there", msg.get_content())

    def test_json_body(self):
        body = json.dumps({"email": "ada@example.com", "message": "Hi"}).encode()
        status, _ = contact.handle(body, "application/json", ENV, lambda *a: None)
        self.assertEqual(status, 200)

    def test_honeypot_sends_nothing(self):
        sender = mock.Mock()
        status, _ = contact.handle(FORM + b"bot", "application/x-www-form-urlencoded", ENV, sender)
        self.assertEqual(status, 200)
        sender.assert_not_called()

    def test_requires_email_and_message(self):
        for body in (b"email=ada%40example.com", b"message=Hi", b"email=nope&message=Hi"):
            status, _ = contact.handle(body, "application/x-www-form-urlencoded", ENV, mock.Mock())
            self.assertEqual(status, 400)

    def test_length_limit(self):
        body = b"email=ada%40example.com&message=" + b"x" * 5001
        status, _ = contact.handle(body, "application/x-www-form-urlencoded", ENV, mock.Mock())
        self.assertEqual(status, 400)

    def test_no_header_injection(self):
        sent = []
        body = b"name=Ada%0D%0ABcc%3A+x%40evil.com&email=ada%40example.com&message=Hi"
        contact.handle(body, "application/x-www-form-urlencoded", ENV, lambda m, u, p: sent.append(m))
        self.assertIsNone(sent[0]["Bcc"])
        self.assertNotIn("\n", sent[0]["Subject"])

    def test_off_without_password(self):
        sender = mock.Mock()
        status, result = contact.handle(FORM, "application/x-www-form-urlencoded", {}, sender)
        self.assertEqual(status, 503)
        self.assertIn("comms@dogwoof.ai", result)
        sender.assert_not_called()

    def test_smtp_failure(self):
        def fail(*a):
            raise OSError("down")
        status, _ = contact.handle(FORM, "application/x-www-form-urlencoded", ENV, fail)
        self.assertEqual(status, 502)


class Server(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), contact.handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.sent = []
        patcher = mock.patch.object(contact, "send", lambda m, u, p: self.sent.append(m))
        patcher.start()
        self.addCleanup(patcher.stop)
        env = mock.patch.dict(contact.os.environ, ENV)
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def post(self, body, accept="text/html"):
        conn = http.client.HTTPConnection(*self.server.server_address)
        conn.request("POST", "/api/contact", body, {
            "Content-Type": "application/x-www-form-urlencoded", "Accept": accept})
        return conn.getresponse()

    def test_plain_post_redirects(self):
        r = self.post(FORM)
        self.assertEqual(r.status, 303)
        self.assertEqual(r.getheader("Location"), "/contact?sent=1#form")
        self.assertEqual(len(self.sent), 1)

    def test_json_reply(self):
        r = self.post(b"email=bad&message=Hi", "application/json")
        self.assertEqual(r.status, 400)
        self.assertFalse(json.loads(r.read())["ok"])


if __name__ == "__main__":
    unittest.main()
