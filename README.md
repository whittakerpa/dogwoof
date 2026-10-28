# DogwoofAI website

The public website for DogwoofAI, at dogwoof.ai. Static HTML on Vercel, no build step.

- `index.html`: home
- `intelligence.html`, `storyos.html`, `studio.html`, `originals.html`, `lab.html`, `impact.html`, `about.html`, `contact.html`, `privacy.html`: served at /intelligence, /storyos and so on
- `partials/header.html` and `partials/footer.html`: the one header and footer for every page. Edit them, then run `python3 scripts/layout.py` to copy them into each page, and `python3 scripts/layout.py --check` before committing (it also checks internal links, old contact addresses and the brand spelling)
- `styles.css`: shared styles
- `vercel.json`: clean URLs and basic security headers
- `api/contact.py`: the contact form. Emails each message from comms@dogwoof.ai to itself, Reply-To the visitor; stores and logs nothing. Set `SMTP_USER` (comms@dogwoof.ai) and `SMTP_PASSWORD` (a Google app password for that account) in Vercel → Settings → Environment Variables. Until then the form asks people to email directly. Tests: `python3 -m unittest discover tests`

Vercel: import this repo as its own project, then add dogwoof.ai under Settings → Domains (A record `@` → the address Vercel shows).

## Brand name

The brand is **DogwoofAI**, always one word (also `dogwoofai`, `DOGWOOFAI`), so the brand stays clearly distinct. Never write "Dogwoof AI", "Dogwoof Ai" or "Dogwoof-AI". The legal entity is Dogwoof Pte. Ltd.; the domain and email stay dogwoof.ai. `python3 scripts/layout.py --check` fails on the unapproved spellings.
