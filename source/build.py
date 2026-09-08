#!/usr/bin/env python3
"""Moonshine website builder.

Renders templates/ + data/ into dist/ as plain HTML, CSS and JS.
Squarespace-shaped on purpose: every page is sections, events are data,
so the port later is copy and paste rather than a rebuild.

    python3 build.py            # build once
    SITE_TODAY=2026-09-08 python3 build.py   # pin "today" for past/upcoming
"""
import datetime as dt
import json
import os
import re
import shutil
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
DIST, TPL, DATA, STATIC = ROOT / "dist", ROOT / "templates", ROOT / "data", ROOT / "static"
LONDON = ZoneInfo("Europe/London")


def load(name):
    return json.loads((DATA / name).read_text())


venue = load("venue.json")
events_raw = load("events.json")
faqs = load("faqs.json")
manifest_path = STATIC / "img" / "manifest.json"
images = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

CUSTOM_FONTS = any(
    (STATIC / "fonts" / f).exists()
    for f in ("Perandory-Condensed.woff2", "Perandory-Condensed.otf", "Symphony.woff2", "Symphony.otf")
)
BASE = os.environ.get("BASE_PATH", "").rstrip("/")   # e.g. /moonshine-site-a for GitHub Pages
SITE = (os.environ.get("SITE_URL") or venue["site_url"]).rstrip("/")
TODAY = dt.date.fromisoformat(os.environ["SITE_TODAY"]) if os.environ.get("SITE_TODAY") else dt.date.today()

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
TYPES = {
    "live": "Live Music",
    "dj": "DJs",
    "thursday": "Thursday Events",
    "brunch": "Bottomless Brunch",
    "special": "Special Events",
}
ROOMS = {r["slug"]: r for r in venue["rooms"]}


def fmt_date(d):
    return f"{d.strftime('%a')} {d.day} {MONTHS[d.month - 1]} {d.year}"


def fmt_time(t):
    h, m = map(int, t.split(":"))
    suffix = "am" if h < 12 else "pm"
    h12 = h % 12 or 12
    return f"{h12}{suffix}" if m == 0 else f"{h12}.{m:02d}{suffix}"


def enrich(e):
    e = dict(e)
    d = dt.date.fromisoformat(e["date"])
    e["_date"] = d
    e["date_label"] = fmt_date(d)
    e["date_short"] = f"{d.strftime('%a')} {d.day} {MONTHS[d.month - 1]}"
    e["time_label"] = fmt_time(e["start"]) if e.get("start") else ""
    e["is_past"] = d < TODAY
    e["month_key"] = d.strftime("%Y-%m")
    e["month_label"] = f"{d.strftime('%B')} {d.year}"
    e["url"] = f"/whats-on/{e['slug']}/"
    e["abs_url"] = SITE + e["url"]
    e["type_label"] = TYPES.get(e["type"], e["type"])
    # Friday and Thursday nights also have a DJ, so they answer to the DJs filter too
    extra = {"fridays": ["dj"], "thursdays": ["dj"]}.get(e.get("series_key") or "", [])
    e["tags"] = " ".join(dict.fromkeys([e["type"]] + extra))
    room = ROOMS.get(e.get("room"))
    e["room_name"] = room["name"] if room else ""
    e["room_short"] = room["short"] if room else ""
    if e.get("start"):
        sh, sm = map(int, e["start"].split(":"))
        start = dt.datetime.combine(d, dt.time(sh, sm), tzinfo=LONDON)
        e["iso_start"] = start.isoformat()
        if e.get("end"):
            eh, em = map(int, e["end"].split(":"))
            end_day = d + dt.timedelta(days=1) if (eh, em) <= (sh, sm) else d
            e["iso_end"] = dt.datetime.combine(end_day, dt.time(eh, em), tzinfo=LONDON).isoformat()
    else:
        e["iso_start"] = d.isoformat()
    e["genre_line"] = " · ".join(e.get("genres", []))
    e.setdefault("status", "scheduled")
    e.setdefault("entry", "free")
    e["search"] = " ".join(
        [e["title"], e.get("series", "") or "", e["genre_line"], e["room_name"], e["type_label"], e["month_label"]]
    ).lower()
    return e


events = sorted((enrich(e) for e in events_raw), key=lambda e: (e["_date"], e.get("start", "")))
upcoming = [e for e in events if not e["is_past"]]
past = [e for e in events if e["is_past"]][::-1]
months = []
for e in upcoming:
    if e["month_key"] not in [m["key"] for m in months]:
        months.append({"key": e["month_key"], "label": e["month_label"]})


# ---------- structured data ----------
def address_ld():
    a = venue["address"]
    return {
        "@type": "PostalAddress",
        "streetAddress": a["street"],
        "addressLocality": a["city"],
        "postalCode": a["postcode"],
        "addressCountry": "GB",
    }


def venue_ld():
    return {
        "@context": "https://schema.org",
        "@type": "BarOrPub",
        "@id": SITE + "/#venue",
        "name": venue["name"],
        "alternateName": venue["legal_name"],
        "description": venue["description"],
        "url": SITE + "/",
        "telephone": venue["phone_intl"],
        "email": venue["email"],
        "image": [SITE + "/static/img/og-default.jpg"],
        "logo": SITE + "/static/img/logo.png",
        "priceRange": "££",
        "address": address_ld(),
        "hasMap": venue["maps_url"],
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["day"], "opens": h["opens"], "closes": h["closes"]}
            for h in venue["hours"]
        ],
        "sameAs": [venue["socials"]["instagram"], venue["socials"]["facebook"]],
        "publicAccess": True,
    }


def event_ld(e):
    is_music = e["type"] in ("live", "dj")
    ld = {
        "@context": "https://schema.org",
        "@type": "MusicEvent" if is_music else "Event",
        "name": e["title"],
        "startDate": e["iso_start"],
        "eventStatus": "https://schema.org/EventCancelled"
        if e["status"] == "cancelled"
        else "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "description": e["blurb"],
        "url": e["abs_url"],
        "image": [f"{SITE}/static/img/{e['image']}.jpg"],
        "location": {"@type": "BarOrPub", "@id": SITE + "/#venue", "name": venue["name"], "address": address_ld()},
        "organizer": {"@type": "Organization", "name": venue["name"], "url": SITE + "/"},
    }
    if e.get("iso_end"):
        ld["endDate"] = e["iso_end"]
    if e.get("artist"):
        perf = {"@type": "MusicGroup" if e.get("artist_is_group") else "Person", "name": e["artist"]}
        if e.get("artist_ig"):
            perf["sameAs"] = [e["artist_ig"]]
        ld["performer"] = perf
    price = "0" if e["entry"] in ("free", "ticket") else str(e.get("price_number", "0"))
    ld["offers"] = {
        "@type": "Offer",
        "url": (e["cta"]["url"] if e["cta"]["url"].startswith("http") else SITE + e["cta"]["url"]),
        "price": price,
        "priceCurrency": "GBP",
        "availability": "https://schema.org/SoldOut" if e["status"] == "sold_out" else "https://schema.org/InStock",
        "validFrom": TODAY.isoformat(),
    }
    if e["status"] == "cancelled":
        del ld["offers"]
    return ld


def breadcrumb_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)
        ],
    }


def itemlist_ld(evs):
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "What's On at Moonshine Leicester",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": e["abs_url"], "name": e["title"]} for i, e in enumerate(evs)
        ],
    }


def faq_ld(groups):
    qs = []
    for g in groups:
        for q in g["items"]:
            qs.append(
                {
                    "@type": "Question",
                    "name": q["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": " ".join(q["a"])},
                }
            )
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qs}



_ATTR = re.compile(r'\b(href|src|content|action|data-resdiary|poster)="(/(?!/)[^"]*)"')
_SRCSET = re.compile(r'\bsrcset="([^"]*)"')


def with_base(html):
    """Prefix every root-absolute URL with BASE so the site works under a
    GitHub Pages subpath. Protocol-relative and absolute URLs are untouched."""
    if not BASE:
        return html
    html = _ATTR.sub(lambda m: f'{m.group(1)}="{BASE}{m.group(2)}"', html)

    def srcset(m):
        out = []
        for part in m.group(1).split(","):
            part = part.strip()
            if part.startswith("/") and not part.startswith("//"):
                part = BASE + part
            out.append(part)
        return 'srcset="' + ", ".join(out) + '"'

    return _SRCSET.sub(srcset, html)


# ---------- rendering ----------
env = Environment(
    loader=FileSystemLoader(TPL),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals.update(images=images, base=BASE)
env.filters["ld"] = lambda o: json.dumps(o, ensure_ascii=False)

sitemap = []


def render(template, out, page, **ctx):
    page = dict(page)
    page.setdefault("url", out)
    # every interior page gets breadcrumbs unless the template passes its own
    if "breadcrumb_ld" not in ctx and out != "/" and not page.get("noindex"):
        crumb = page.get("crumb") or next(
            (l["label"] for l in venue["footer_links"] + venue["nav"] if l["url"] == out), None
        ) or page["title"].split("|")[0].strip()
        ctx["breadcrumb_ld"] = json.dumps(breadcrumb_ld([("Home", "/"), (crumb, out)]), ensure_ascii=False)
    ctx.setdefault("book_url", "/book-a-table/")
    ctx.update(
        base=BASE,
        venue=venue,
        site_url=SITE,
        year=TODAY.year,
        today=TODAY,
        today_iso=TODAY.isoformat(),
        upcoming=upcoming,
        past=past,
        months=months,
        faqs=faqs,
        rooms=venue["rooms"],
        venue_ld=json.dumps(venue_ld(), ensure_ascii=False),
        custom_fonts=CUSTOM_FONTS,
        page=page,
    )
    html = with_base(env.get_template(template).render(**ctx))
    target = DIST / out.lstrip("/")
    if out.endswith("/"):
        target = target / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)
    if not page.get("noindex"):
        sitemap.append((out, page.get("priority", "0.6"), page.get("changefreq", "monthly")))
    return out


def build():
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir(parents=True)
    shutil.copytree(STATIC, DIST / "static", ignore=shutil.ignore_patterns("src", ".DS_Store"))
    if BASE:
        # stylesheets carry their own root-absolute url(), e.g. the @font-face files
        for css in (DIST / "static").rglob("*.css"):
            t = css.read_text()
            if "url(/" in t:
                css.write_text(re.sub(r"url\((/(?!/))", f"url({BASE}/", t))

    render(
        "home.html",
        "/",
        {
            "title": "Moonshine Leicester | Speakeasy Bar, Live Music & Cocktails",
            "description": "Step inside Moonshine, Leicester's iconic speakeasy bar for cocktails, live music, DJs, bottomless brunch, table bookings and private hire.",
            "priority": "1.0",
            "changefreq": "weekly",
        },
        next_events=upcoming[:4],
    )
    render(
        "whats-on.html",
        "/whats-on/",
        {
            "title": "What's On at Moonshine | Live Music & Events Leicester",
            "description": "Discover live music, DJs, performers and special events at Moonshine Leicester. Explore upcoming dates and reserve your table.",
            "priority": "0.9",
            "changefreq": "weekly",
        },
        events=upcoming,
        itemlist_ld=json.dumps(itemlist_ld(upcoming), ensure_ascii=False),
        breadcrumb_ld=json.dumps(breadcrumb_ld([("Home", "/"), ("What's On", "/whats-on/")]), ensure_ascii=False),
    )
    for e in events:
        related = [x for x in upcoming if x["slug"] != e["slug"] and x["type"] == e["type"]][:3] or upcoming[:3]
        render(
            "event.html",
            e["url"],
            {
                "title": f"{e['title']} | {e['date_label']} | Moonshine Leicester",
                "description": (e["blurb"][:150] + "…") if len(e["blurb"]) > 150 else e["blurb"],
                "og_image": e["image"],
                "og_type": "article",
                "priority": "0.5" if e["is_past"] else "0.8",
                "changefreq": "yearly" if e["is_past"] else "weekly",
            },
            e=e,
            related=related,
            book_url=f"/book-a-table/?date={e['date']}",
            event_ld=json.dumps(event_ld(e), ensure_ascii=False),
            breadcrumb_ld=json.dumps(
                breadcrumb_ld([("Home", "/"), ("What's On", "/whats-on/"), (e["title"], e["url"])]), ensure_ascii=False
            ),
        )
    render(
        "brunch.html",
        "/bottomless-brunch-leicester/",
        {
            "title": "Bottomless Brunch Leicester | Live Entertainment at Moonshine",
            "description": "Book Moonshine Bottomless Brunch in Leicester - 90 minutes of prosecco, draught beer and soft drinks, a bubbly cocktail kit, grazing boards and live entertainment for £45 per person.",
            "priority": "0.9",
            "changefreq": "weekly",
        },
        brunch_events=[x for x in upcoming if x["type"] == "brunch"],
        brunch_faqs=next((g for g in faqs if g["key"] == "brunch"), None),
    )
    render(
        "private-hire.html",
        "/private-hire-leicester/",
        {
            "title": "Private Hire Leicester | Event Spaces at Moonshine",
            "description": "Hire Moonshine Leicester for birthdays, corporate events, celebrations and private parties. Explore the Speakeasy Bar, Members Bar and Sports Bar.",
            "priority": "0.9",
        },
        hire_rooms=[r for r in venue["rooms"] if r.get("hire")],
    )
    render(
        "host-your-event.html",
        "/host-your-event/",
        {
            "title": "Host an Event at Moonshine Leicester | Creative Venue Collaboration",
            "description": "Bring your public event idea to Moonshine Leicester. We welcome live music, spoken word, comedy, workshops, paint and sip events, launches and new concepts.",
            "priority": "0.8",
        },
    )
    render(
        "faqs.html",
        "/faqs/",
        {
            "title": "Moonshine Leicester FAQs | Bookings, Dress Code, Access & More",
            "description": "Plan your visit to Moonshine Leicester with answers about bookings, opening hours, dress code, age policy, accessibility, bottomless brunch and private hire.",
            "priority": "0.7",
        },
        faq_ld=json.dumps(faq_ld(faqs), ensure_ascii=False),
    )
    render(
        "contact.html",
        "/contact/",
        {
            "title": "Contact Moonshine Leicester | 91 High Street, LE1 4JB",
            "description": "Contact Moonshine Leicester, find opening hours and plan your visit to our speakeasy bar at 91 High Street in Leicester city centre.",
            "priority": "0.7",
        },
    )
    render(
        "about.html",
        "/about-moonshine/",
        {
            "title": "About Moonshine | Leicester's Speakeasy Bar",
            "description": "Discover Moonshine, Leicester's atmospheric speakeasy bar for live music, cocktails, DJs, events and late-night experiences at 91 High Street.",
            "priority": "0.6",
        },
    )
    render(
        "book-a-table.html",
        "/book-a-table/",
        {
            "title": "Book a Table at Moonshine Leicester",
            "description": "Reserve your table at Moonshine Leicester and choose from the Theatre Stage, Speakeasy Bar, Sports Bar or Members Bar, subject to availability.",
            "priority": "0.9",
        },
    )
    # system pages, no index
    simple = [
        (
            "/book-a-table/confirmed/",
            "Booking confirmed | Moonshine Leicester",
            "Confirmed booking",
            "<p>Your table is confirmed. We have sent the booking details to your email address. Please check the date, arrival time, area and booking terms before your visit.</p><p>Questions? Call <a href=\"tel:{tel}\">{phone}</a> or <a href=\"/contact/\">contact the team</a>.</p>",
        ),
        (
            "/book-a-table/request-received/",
            "Booking request received | Moonshine Leicester",
            "Request received",
            "<p>We have received your booking request. This is not yet a confirmed reservation. The team will contact you using the details provided once availability has been checked.</p>",
        ),
        (
            "/enquiry-received/",
            "Enquiry received | Moonshine Leicester",
            "Your message has reached the Moonshine team.",
            "<p>We will use your details to respond to this enquiry. Marketing consent is optional and separate.</p><p>In the meantime, take a look at <a href=\"/whats-on/\">what's on</a>.</p>",
        ),
        (
            "/privacy/",
            "Privacy | Moonshine Leicester",
            "Privacy",
            "<p>Privacy policy to be supplied by Moonshine before launch. This page explains what personal data the venue collects through bookings, enquiries and the newsletter, and how it is used and kept.</p>",
        ),
        (
            "/cookies/",
            "Cookies | Moonshine Leicester",
            "Cookies",
            "<p>Cookie policy to be supplied before launch. The booking widget and any analytics will be listed here with a way to change your consent.</p>",
        ),
        (
            "/terms/",
            "Terms | Moonshine Leicester",
            "Terms",
            "<p>Booking terms, cancellation and amendment policy, and house rules to be supplied by Moonshine before launch.</p>",
        ),
        (
            "/accessibility/",
            "Accessibility | Moonshine Leicester",
            "Accessibility",
            "<p>An accessible lift is available at the venue. When you arrive, speak to a member of our door team at the main entrance and they will be happy to assist you.</p><p>If anything on this website is difficult to use, <a href=\"/contact/\">tell us</a> and we will fix it.</p>",
        ),
    ]
    for url, title, heading, body in simple:
        render(
            "simple.html",
            url,
            {"title": title, "description": title, "noindex": True},
            heading=heading,
            body_html=body.format(tel=venue["phone_tel"], phone=venue["phone"]),
        )
    render(
        "simple.html",
        "/404.html",
        {"title": "Page not found | Moonshine Leicester", "description": "Page not found", "noindex": True, "url": "/404.html"},
        heading="This door leads nowhere.",
        body_html="<p>The page you were looking for is not here. Try <a href=\"/whats-on/\">what's on</a>, <a href=\"/book-a-table/\">book a table</a> or head <a href=\"/\">back to the start</a>.</p>",
    )

    # sitemap + robots
    lastmod = TODAY.isoformat()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, prio, freq in sitemap:
        xml.append(
            f"  <url><loc>{SITE}{url}</loc><lastmod>{lastmod}</lastmod><changefreq>{freq}</changefreq><priority>{prio}</priority></url>"
        )
    xml.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(xml))
    if os.environ.get("PREVIEW"):
        (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    else:
        (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")

    print(f"built {len(sitemap)} indexable pages, {len(events)} events ({len(upcoming)} upcoming, {len(past)} past) -> {DIST}")


if __name__ == "__main__":
    build()
