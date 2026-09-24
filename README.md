# Wayside site

The public pages App Review requires: a one-page site, the privacy policy and a support page.
Static HTML and one stylesheet, no build step.

```
index.html        the app page
privacy/          the privacy policy, linked from About and from App Store Connect
support/          the support page, linked from About
style.css         shared, light and dark
icon.png          the app icon at 256px
test-provider/    a pretend camera database and release feed that debug builds import to test a second provider
```

## Publishing

The app's own repository is private, so these pages live in a **separate public repository** —
GitHub Pages only serves from a public repository on a free plan. They are published from
[waysideapp/website](https://github.com/waysideapp/website): copy this directory into it, then
Settings → Pages → Deploy from a branch → `main` → `/ (root)`. That repository's issues are also
the support channel the support page points at.

## The domain

**getwayside.app**, registered through IONOS and pointed at GitHub Pages:

- **Apex**: four A records to `185.199.108.153`, `185.199.109.153`, `185.199.110.153` and
  `185.199.111.153`. Confirm these against GitHub's current documentation before relying on them.
- **Subdomain**: `www` as a CNAME to `waysideapp.github.io`.
- **Ownership**: a `_github-pages-challenge-waysideapp` TXT record, added by Settings → Pages.

A challenge record is per owner, so moving the repository between accounts means adding the new
owner's record before the move and removing the old one after. Both may exist at once.

`.app` is on the HSTS preload list, so nothing loads at all until GitHub has issued the
certificate and Enforce HTTPS is on. The two URLs the app opens live in
`Wayside/App/AppLinks.swift` and must match whatever this resolves to.

## Keeping the policy honest

This is the only copy of the privacy policy; the markdown that used to sit in `docs/` is gone, so
there is nothing to drift out of step. When the app gains anything that touches data — a new
permission, a new thing shown on the Lock Screen, a new export — change `privacy/index.html`, the
Data Privacy page in the app, and the date at the top of both.
