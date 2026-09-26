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
community-db/     the community camera database the app downloads, rebuilt weekly by the workflow in .github/
```

## Publishing

The app's own repository is private, so these pages live in a **separate public repository** —
GitHub Pages only serves from a public repository on a free plan. They are published from
[waysideapp/website](https://github.com/waysideapp/website): copy this directory into it, then
Settings → Pages → Deploy from a branch → `main` → `/ (root)`. That repository's issues are also
the support channel the support page points at.

Copy the dot-directory too, since the workflow lives there:

```bash
cp -R site/. ../website/
```

The copy overwrites what is in both places and leaves the rest alone, so the database files
the workflow commits over there survive it.

## The community database

`community-db/build.py` fetches Lufop.net's EU archive, keeps the GB files, and writes
`gb-cameras.zip` and `manifest.json` beside itself. `.github/workflows/community-db.yml`
runs it every Sunday at 06:30 UTC and commits the result, and the app fetches the ZIP from
`https://getwayside.app/community-db/gb-cameras.zip` (the URL is `LufopSource.releaseURL`).
Neither output file is kept in this repository: they are produced in the website repository
only, by the workflow.

- **After the first copy**, run the workflow by hand (Actions → Community database → Run
  workflow). Until it has run once the app's download returns 404, which it treats as a
  failed weekly refresh and keeps the cameras it has.
- **lufop.net refuses GitHub's runners.** Its Cloudflare front has answered them with 403
  since September 2026, which is also why the Open-GATSO-POI build stopped. The workflow
  still tries the download first, and when it fails builds from
  `community-db/source/lufop-eu.zip`, a copy of the archive committed here by hand. The
  manifest's `fetched` says which happened. To refresh the copy, download
  `Lufop-Zones-de-danger-EU-CSV.zip` from
  [lufop.net's download page](https://lufop.net/zones-de-danger-france-et-europe-asc-et-csv/)
  in a browser, save it over that path, commit it and run the workflow. The data is
  CC BY-SA 4.0, so keeping the copy here is allowed. Without a copy, a refused download
  fails the run and the published files stay as they were.
- **A failed run leaves the last files in place.** The script refuses to publish fewer than
  4,000 cameras, or a dataset with no red-light or no fixed cameras. It cannot be tested
  against lufop.net from a laptop either; test it with `--source` and a copy of the archive.
- **The schedule needs commits.** GitHub disables a public repository's scheduled workflows
  after 60 days without activity, which is why the manifest's `checkedAt` changes on every
  run and every run commits.
- **Only fixed and red-light files are read.** Lufop's GB set has nothing else today; a
  section (`Troncondebut`) or tunnel file that appeared would be listed under `ignoredFiles`
  in the manifest rather than published as a fixed camera.

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
