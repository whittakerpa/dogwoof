# dogwoof

Holding page for dogwoof.ai. Static HTML on Vercel, no build step.

- `index.html`: home
- `intelligence.html`, `storyos.html`, `studio.html`, `originals.html`, `lab.html`, `impact.html`, `about.html`, `contact.html`, `privacy.html`: served at /intelligence, /storyos and so on
- `partials/footer.html`: the one footer for every page. Edit it, then run `python3 scripts/footer.py` to copy it into each page, and `python3 scripts/footer.py --check` before committing (it also checks internal links and old contact addresses)
- `styles.css`: shared styles
- `vercel.json`: clean URLs and basic security headers

Vercel: import this repo as its own project, then add dogwoof.ai under Settings → Domains (A record `@` → the address Vercel shows).
