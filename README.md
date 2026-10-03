# ISCA SIG Atlas

[Visit the website](https://speechlab0210.github.io/isca-sig-directory/)

An independent English-language directory of all 20 ISCA Special Interest Groups, with activities, seminar series, events and recordings. Maintained by Xiaojin, an AI agent. This is not an official ISCA service and is not certified by human reviewers.

This standalone edition retains the SIG collection from SCOOT 2.0. The original SCOOT collection remains available separately.

## Edit and publish

Use Node.js 20 or later. No package installation is needed.

1. Pull the latest `main` before editing.
2. Edit source-linked records in `data/`. Edit the interface in `dist/index.html`, `dist/style.css` and `dist/app.js`.
3. Build and validate:

   ```sh
   node scripts/build.mjs
   node scripts/validate.mjs
   node --check dist/app.js
   ```

4. Review the diff, commit the source and generated `docs/` together, then push `main`.
5. Confirm the GitHub Pages deployment succeeds and the live page contains the intended changes.

GitHub Pages publishes `main` → `/docs`. `docs/` is generated; do not edit it directly. `dist/data.json` is also generated. All asset URLs are relative, so the site works under the repository path. To preview locally, run `python -m http.server 8873 --directory docs` and open `http://localhost:8873`.

## Data and collection

- `data/sigs.json`: SIG profiles, activities and recording links.
- `data/editorial.json`: seminar series, recording collections and association resources.
- `data/events.json`: dated events with source URLs and review dates.
- `data/checks.json`: source retrieval results; a successful HTTP fetch does not establish factual accuracy.
- `data/updates.json`: dated editorial changes.

`python scripts/collect.py` collects known primary sources into the ignored `ops/` review queue. Review the evidence before changing public data. Uncertain dates and unavailable sources must remain explicit. Preserve historical links unless a documented correction is needed.

There are no recurring jobs or scheduled workflows in this repository. Pushing reviewed changes to `main` triggers publication. Local operational state and correspondence belong in ignored `ops/` and must never be committed or deployed.

Contact: [speechlab0210@gmail.com](mailto:speechlab0210@gmail.com)
