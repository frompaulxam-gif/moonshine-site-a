# Moonshine Leicester, website option A

A working preview of a new website for Moonshine Speakeasy, 91 High Street, Leicester.

**Live preview: https://frompaulxam-gif.github.io/moonshine-site-a/**

Built from Chelsea's "Website Strategy & Content Specification" brief. Look and feel
takes from 58th Street, the What's On section takes its mechanics from Ronnie Scott's
find-a-show.

## What is here

- **Root of this repo** is the built site, served by GitHub Pages.
- **`source/`** is everything it is generated from: `build.py`, the Jinja templates,
  the JSON data and the CSS. Run `python3 source/build.py` to rebuild.

## The site

43 pages. Home, What's On (34 events, one page each, filters by type, room, month and
free text, grid or by-date view), Bottomless Brunch, Private Hire, Host Your Event,
FAQs, Contact, About, Book a Table, a designed 404 and the legal stubs.

Every event is real text, not a poster image. That is the core fix: the current
moonshineleicester.co.uk publishes its line-ups as flat JPEGs, so Google cannot read a
single artist name or date.

SEO built in: per-page titles, meta descriptions, canonicals and share images;
BarOrPub schema with address, phone and opening hours; MusicEvent or Event schema on
every event page; ItemList on What's On; FAQPage schema; breadcrumbs; sitemap.

Bookings use the venue's live ResDiary calendar. A Book a Table button on any event
opens the calendar already set to that night.

## Placeholders in this preview

- **Hero video** is cut from the Ringlight footage of 6 September. Manjo's video replaces it.
- **Fonts** fall back to Bodoni and Pinyon Script. The licensed Perandory Condensed and
  Symphony drop into `source/static/fonts/` and the build links them automatically.
- **Photography** is pulled from the current site and the Instagram grid, pending Chelsea's selection.
- **Forms** validate and confirm but send nothing. They become native form blocks on Squarespace.
- The raw 4K video originals are not in this repo. They stay on the source machine.

This preview is set to noindex so it cannot compete with the live venue site in search.

Intended destination is Squarespace. `source/README.md` has the porting notes.
