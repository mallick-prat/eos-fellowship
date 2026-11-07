# Eos Fellowship website

The Eos Fellowship site, styled as an illuminated medieval manuscript.

- Live: https://eosfellows.com (application page: https://eosfellows.com/apply). Also served at https://eos-fellowship.vercel.app.
- Campus shortcuts like eosfellows.com/princeton redirect to that session's Partiful page; they live in `vercel.json`.
- Mirror: https://mallick-prat.github.io/eos-fellowship/
- Applications go to the Google Sheet **Eos Fellowship Applications** (owned by mallickprat@gmail.com). Each applicant is emailed a copy.

## What's in here

| Path | What it is |
|---|---|
| `index.html`, `apply.html`, `404.html` | The built pages. These are what get deployed. Don't edit them by hand; edit `src/` and rebuild. `404.html` is the "page is missing" page Vercel shows for any address that doesn't exist. |
| `robots.txt`, `sitemap.xml` | For search engines. Also made by the build. |
| `og.jpg`, `favicon*`, `icon-192.png`, `apple-touch-icon*.png` | Social preview card and icons, made by `tools/social.py`. The browser-tab icon (`favicon.*`) is the logo's sun in Eos blue; the home-screen icons are the gold sun miniature. |
| `src/site.json` | Info sessions (school, Partiful ID, date and time), the Sheet endpoint, the site URL, and the preview tagline. |
| `src/links.json` | LinkedIn URLs, company websites, and mentor titles. |
| `src/templates/` | The page: `head.html` (styles, header), `index.body.html`, `apply.body.html`, `404.body.html`, `script.html` (menu, sessions, form, analytics events). |
| `src/assets/` | Manuscript scans (border, initials, drolleries), the Partiful posters, and the logo traced into SVG paths. |
| `google-apps-script.js` | The Apps Script behind the Sheet: saves each application and emails the copy. |
| `tools/` | Build and asset scripts (see below). |

## Making a change

1. Edit `src/`, not `index.html` (the build overwrites it). For example, change a session's time in `src/site.json`;
   sessions outside Eastern time also set `tz` and `utc_offset`, as Berkeley and Stanford do.
2. Rebuild: `python3 tools/build.py`
3. Look at `index.html` / `apply.html` in a browser.
4. Deploy:
   ```bash
   git add -A && git commit -m "Describe the change" && git push
   ```
   Vercel and GitHub Pages both deploy automatically from the push. (`vercel deploy --prod --yes` from the repo root
   also works; it's linked to the `eos-fellowship` project in the *Pratyush Mallick's projects* team.)
   `.vercelignore` keeps `src/` and `tools/` out of the deploy.

`python3 tools/build.py --preview` also writes `preview/` (git-ignored), the copy used for the claude.ai artifact
preview. Its form points people to the live site, because artifacts can't send data to Google.

## Traffic analytics

Vercel Web Analytics is on for the project. See it at
https://vercel.com/pratyush-mallicks-projects/eos-fellowship/analytics: visitors, page views, referrers,
countries and devices. It uses no cookies, so the site needs no cookie banner. Only the Vercel-hosted site is
counted, not the GitHub Pages mirror.

Under **Events** in the same dashboard (`script.html` sends these):

| Event | When | Details |
|---|---|---|
| `RSVP` | Someone clicks a session's RSVP button or poster | `campus` |
| `Add to calendar` | Someone clicks a session's calendar link | `campus` |
| `Apply click` | Someone clicks an Apply link | `from`: header, hero, apply (How to apply), footer |
| `Application started` | First keystroke in the form | |
| `Application submitted` | The form is sent | `school`, `level`, `year`. Never names or contact details. |
| `Page not found` | Someone lands on a missing page | `path`, so broken links can be found |

Campus shortcuts (eosfellows.com/penn etc.) redirect before any page loads, so Web Analytics can't count
them. Their hits are in the request logs: `vercel logs requests --since 24h --query 'requestPath:"/penn"'`.

## Changing the preview card or icons

Edit the tagline in `src/site.json`, then run `python3 tools/social.py`. This needs Google Chrome and ImageMagick.
Social sites cache previews, so a changed card can take a while to show up where the link was already shared.

## The application Sheet

- Each submission is a row in the **Applications** tab. "Copy emailed" records whether the confirmation went out.
- Gmail allows about 100 of these emails a day. Past that, applications still save; only the email is skipped.
- Each address gets at most one copy a day, so the form can't be used to flood someone's inbox.
- To change the script, edit it in Apps Script (Extensions → Apps Script in the Sheet) and keep
  `google-apps-script.js` in sync. Redeploy with **Deploy → Manage deployments → Edit → New version**, so the
  `/exec` URL in `src/site.json` stays the same.

## Rebuilding the assets (rarely needed)

- `tools/split_logo.py src/assets/source/eos-logo.svg src/assets` splits the logo into the sun outline, the sun linework, and the wordmark.
- `tools/lift_parchment.py <scan.png> <out.png> 226 221 202` makes a scan's parchment transparent so it sits on the page.
- `tools/patch_border.py <in.png> <out.png>` removes the small figure from the border's right edge so it can repeat.
  `src/assets/source/border-original.png` is the untouched scan.

## Credits

Borders, initials and drolleries are details from medieval manuscripts (a Troyes Book of Hours, 1415–20; the
Breviary of Renaud de Bar, 1302–03; a Bruges Book of Hours, 1510–25; the Luttrell Psalter, c. 1325–40; and others),
gathered by the [Hellmouth Manuscript Maker](https://hell-mouth.neocities.org/manuscript).
