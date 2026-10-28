# dogwoof

Holding page for dogwoof.ai. Static HTML on Vercel, no build step.

- `index.html`: home
- `storyos.html`, `originals.html`, `about.html`, `intelligence.html`, `impact.html`: served at /storyos, /originals, /about, /intelligence, /impact
- `styles.css`: shared styles
- `vercel.json`: clean URLs and basic security headers

Vercel: import this repo as its own project, then add dogwoof.ai under Settings → Domains (A record `@` → the address Vercel shows).
