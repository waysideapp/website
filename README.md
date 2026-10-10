# Wayside website

The website for [Wayside](https://getwayside.app), a speed camera alert app for iPhone. It
holds the home page, the privacy policy, the support page and the community camera database
the app downloads. Everything is static HTML and one stylesheet, with no build step.

```
index.html        the home page
privacy/          the privacy policy
support/          the support page
style.css         shared styles, light and dark
icon.png          the app icon at 256px
community-db/     the community camera database, rebuilt weekly by the workflow in .github/
test-provider/    an invented camera database and release feed, used to test imports
```

## Publishing

GitHub Pages serves `main` from the repository root. A merge to `main` goes live within about
a minute.

## The community database

`community-db/build.py` downloads Lufop.net's EU archive, keeps the Great Britain files, and
writes `gb-cameras.zip` and `manifest.json` next to itself. The app downloads
`https://getwayside.app/community-db/gb-cameras.zip`. The workflow in
`.github/workflows/community-db.yml` runs the script every Sunday at 06:30 UTC and commits
the result. Only the workflow should change the two output files. Don't edit them by hand.

- **Running it by hand.** Go to Actions → Community database → Run workflow.
- **Building from a saved copy.** lufop.net has blocked GitHub's runners since September
  2026. When the download fails, the workflow builds from
  `community-db/source/lufop-eu.zip`, a copy of the archive committed by hand. The
  manifest's `fetched` field shows which source was used. To refresh the copy, sign in at
  lufop.net and download `Lufop-Zones-de-danger-EU-CSV.zip` from
  [the download page](https://lufop.net/zones-de-danger-france-et-europe-asc-et-csv/).
  You need a free account, and ad blockers can hide the link. Save the file over the
  committed copy, commit it and run the workflow. Don't automate the sign-in.
- **When a run fails.** The last published files stay in place. The script won't publish a
  dataset with fewer than 4,000 cameras, or one with no red-light or no fixed cameras. To
  test it locally, run it with `--source` and a copy of the archive.
- **Why every run commits.** GitHub turns off scheduled workflows in a public repository
  after 60 days without activity. The manifest's `checkedAt` field changes on every run,
  so every run makes a commit.
- **Which files are used.** The script reads only Lufop's fixed and red-light camera files.
  Any other kind of file, such as a tunnel or average speed section, is listed under
  `ignoredFiles` in the manifest and not published.

## The domain

getwayside.app is a GitHub Pages custom domain, set up as GitHub's custom-domain
documentation describes. GitHub verifies the domain for the account that owns the
repository. To move the repository to another account, add the new owner's verification
before the move and remove the old one afterwards. Both can exist at the same time.

`.app` domains only load over HTTPS. The site doesn't load at all until GitHub has issued
the certificate and Enforce HTTPS is on.

## Changing the privacy policy

`privacy/index.html` is the only copy of the privacy policy. When the app starts handling
data in a new way, update the policy here, update the privacy page inside the app to match,
and change the date at the top of both.

## Licence

The camera data in `community-db/` comes from [Lufop.net](https://lufop.net) under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
