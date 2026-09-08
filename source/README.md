# Moonshine Leicester, new website (local build)

The whole new site, built locally first so it can be looked at, iterated and
signed off before it is moved onto Squarespace. Style from 58th Street, What's
On mechanics from Ronnie Scott's, copy from Chelsea's brief, events from the
booking calendar.

## Run it

```bash
cd /Users/paulventura/TDG/moonshine/new-website
python3 build.py
python3 -m http.server 4871 --directory dist
```

Then open http://localhost:4871. In Claude Code the launch entry is `moonshine-site`.

Rebuild after any change to `data/`, `templates/` or `static/`. The build takes
a second. The server reads `dist/` live, no restart needed.

## Folder map

| Path | What |
|---|---|
| `build.py` | Renders templates + data into `dist/`. Also writes sitemap.xml, robots.txt and all structured data |
| `prepare_images.py` | Picks, renames and resizes the photos into `static/img/` with WebP, plus logo, favicons and the share image |
| `data/venue.json` | Address, phone, hours, socials, nav, rooms, the weekly series copy, hero video paths |
| `data/events.json` | Every event. One object each. This is the What's On |
| `data/faqs.json` | The FAQ groups and answers |
| `templates/` | One template per page type. `base.html` is the shell, `macros.html` holds the image, button and event card blocks |
| `static/css/site.css` | All styling. `fonts-custom.css` is linked automatically once the licensed fonts exist |
| `static/js/site.js` | Header, menu, hero video, booking iframe, form stubs, map, booking date note |
| `static/js/whats-on.js` | Filters, search, month jump, paging, grid or list view |
| `static/img/src/` | Raw source photos (not copied to dist) |
| `static/video/` | Hero loop, desktop 16:9 and portrait 9:16 |
| `video-src/` | The Ringlight 4K originals the loop was cut from (not copied to dist) |
| `dist/` | The built site. Never edit here, it is wiped on every build |
| `qc/` | Screenshots and report from the last headless QC pass |

## Editing an event

Add or edit an object in `data/events.json` and rebuild. Fields:

```
slug            URL slug, use name-yyyy-mm-dd
title           Card and page heading
artist          Performer name (optional)
artist_is_group true for bands
artist_ig       Instagram URL. Only add handles marked safe in the booking calendar
date, start, end  ISO date, 24h times
type            live | dj | thursday | brunch | special  (drives the filters)
series_key      thursdays | fridays | saturdays | brunch | null
room            theatre | speakeasy-bar | members-bar | sports-bar
genres          2 to 4 short words, shown as the style line
blurb           One or two sentences, the brief's holding copy templates
image           A name from static/img/manifest.json
entry           free | ticket | paid
price, price_number   For paid events only
status          scheduled | sold_out | cancelled | tbc
cta, cta2       {label, url}. Book a Table links carry ?date= so the booking page can name the night
```

Past events stay live, marked "This event has passed", and drop off the main
grid automatically. "Today" is the machine date; pin it with
`SITE_TODAY=2026-09-08 python3 build.py` when checking.

## What is placeholder right now

- **Fonts.** Preandory Condensed and Symphony are not on this Mac. The stack falls back to Bodoni 72 and Snell Roundhand (installed here) and to Bodoni Moda and Pinyon Script from Google Fonts elsewhere. Drop the real files into `static/fonts/` as `Perandory-Condensed.woff2` and `Symphony.woff2` and rebuild. Nothing else changes.
- **Hero video.** A 15 second silent loop cut from the Ringlight 6 Sept delivery. Manjo's video replaces it: drop the files in `static/video/` and point `hero_video` and `hero_video_portrait` in `venue.json` at them.
- **Photos.** Pulled from the current site and the Instagram grid. Chelsea is selecting the final photography. Swap files in `static/img/src/`, update `prepare_images.py` picks, run it, rebuild.
- **Forms.** Contact, private hire, host your event and newsletter validate and show the success copy but send nothing. On Squarespace they become native form blocks. Anywhere else they need an endpoint.
- **Booking.** The ResDiary calendar is the hosted widget page framed in (`booking.resdiary.com/widget/Standard/Moonshine/68435` for tables, `68894` for brunch). It shows the full calendar on any domain. The script embed from the old site is documented in `site.js` if the live domain prefers it.
- **Map.** Loads Google Maps only when the visitor clicks, no key needed.

## Confirm before anything goes live

From the brief and from building this:

1. Opening hours. Site says Thu 7pm to 12am, Fri 6pm to 3am, Sat 4pm to 3am (the brief's footer). The old site said Thu 6pm and Sat 2am. Fran owns this.
2. Happy hour times in the series copy (Thu all night, Fri 6 to 8, Sat 5 to 7) came from the happy hour graphic. Confirm.
3. Fri 18 Dec: calendar lists both Darcie Edwards and Louis Brown at 9.30pm. Louis Brown is on the site (his tour page confirms). Check.
4. Sat 12 Dec 4.30pm Marcius Riley is listed as Bottomless Brunch, status "date to be confirmed". Confirm it is a brunch.
5. Thu 10 Sept Veda Club gala is not listed. It is a third party ticketed event. Add it if the venue wants it promoted.
6. Thursday rotation (Trivia, Karaoke, Retro Movie, Open Mic) is described but only dated where confirmed (Nola Jam 17 Sept, Open Mic 24 Sept). Add the October dates once Chelsea confirms them.
7. Private hire capacities, prices and minimum spends are not published (brief says never publish placeholders). The fact panel appears automatically once `facts` is filled in `venue.json`.
8. Privacy, cookies, terms and accessibility pages are stubs, marked noindex.
9. Artist Instagram links are only on the acts the booking calendar marks safe. Ellie Jolly, Dana Ali, Emma Mawdsley, Marcius Riley, Metz Jnr, Alex Slater, Sofie Anne have none on purpose.
10. The table booking charge amount and the booking terms are not on the site because they are not in the brief. Once known, put them in the booking band copy next to the calendar.
11. Ticketed nights link to the venue's Fatsoma page. When an event has its own Fatsoma page, put that URL in the event's `cta.url`.
12. Each private hire room shows one photo. The brief asks for a short gallery per room, which waits on the new photography.
13. No guest quotes or press are shown. The brief borrows "social proof" from 58th Street; add real quotes only if the venue supplies them.

## SEO that is built in

Every page has its own title, meta description, canonical and share image.
Sitewide BarOrPub schema with address, phone, hours and social profiles.
Every event page has MusicEvent or Event schema with date, status, performer,
offer and breadcrumbs. The What's On page carries an ItemList of every event.
The FAQ page carries FAQPage schema. `sitemap.xml` and `robots.txt` are
generated. All event copy is real text, none of it is in images.

## Moving it to Squarespace

- Pages map one to one. Each section here is one Squarespace section.
- Events map to a Squarespace Events collection: title, date, time, location (room), excerpt (blurb), body (series copy), category (type), tags (genres). Squarespace adds Event schema to each event page.
- Custom CSS: paste `site.css`. Upload the two licensed fonts in Custom CSS.
- Forms become native form blocks. Newsletter becomes the newsletter block.
- Booking: code block with either the iframe or the script embed.
- The filter bar and grid or list toggle need a code injection block on the What's On page (`whats-on.js` plus the toolbar markup). Everything else is native.

## QC

`qc/` holds the last headless pass: every page at 1440 wide and iPhone 15 Pro,
fold and full page, plus `report.json` with console errors, failed requests,
broken images, horizontal overflow, H1 count and structured data validity.
