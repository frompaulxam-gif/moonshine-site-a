#!/usr/bin/env python3
"""Pick, rename, resize and convert the source photos into static/img/.

Writes JPEG + WebP at up to three widths and a manifest.json with the
dimensions and alt text the templates need. Alt text describes what is
visibly in the frame, per the brief. Run again whenever a photo changes.
"""
import glob
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "static" / "img" / "src"
OUT = ROOT / "static" / "img"
OUT.mkdir(parents=True, exist_ok=True)

IG = sorted(glob.glob(str(SRC / "ig" / "*.jpg")))

# name -> (source, alt)
PICKS = {
    "hero-bar": ("moonshine-header-img.jpg", "Glassware hanging above the Moonshine bar, lit warm"),
    "hero-portrait": ("Moonshine-Francesca_RING8338-scaled.jpg", "A singer in a sequinned dress performing at Moonshine"),
    "bartender-pour": ("speakeasy-bar-leicester.jpg", "A Moonshine bartender pouring a drink at the taps"),
    "cocktails-bar": ("cocktail-bar-leicester.jpg", "Cocktails being poured on the Moonshine bar"),
    "singer-red": ("jazz-bar-leicester.jpg", "A singer at the microphone on the Moonshine stage, lit red"),
    "sax-red": ("live-bands-leicester.jpg", "A saxophonist performing on the Moonshine stage, lit red"),
    "room-theatre": ("Theatre-Stage-2.jpg", "The Theatre Stage at Moonshine, tables set in front of the stage"),
    "room-speakeasy": ("Main-Bar-3.jpg", "Booth seating in the Speakeasy Bar at Moonshine"),
    "room-members": ("Members-Bar-1.jpg", "Booth seating in the Members Bar at Moonshine"),
    "room-sports": ("Sports-Bar-1.jpg", "The pool table and booths in the Sports Bar at Moonshine"),
    "brunch-cheers": ("bottomless-brunch-header.jpg", "Guests raising glasses of prosecco at Bottomless Brunch"),
    "brunch-tower": ("brunch-board-drink.jpg", "A grazing tower and mimosa on a table at Moonshine"),
    "brunch-drinks": ("b05f3267-7805-4c33-8fa3-e88ffe9d5f52.jpg", "A grazing tower with fruit and drinks at Moonshine brunch"),
    "champagne": ("high-angle-foamy-champagne-glass-scaled.jpg", "Glasses of champagne seen from above"),
    "slide-dj-bw": ("slide1-desktop.jpg", "A DJ at the turntables at Moonshine"),
    "slide-bartender-bw": ("slide2-desktop.jpg", "A bartender at work behind the Moonshine bar"),
    "slide-3-bw": ("slide3-desktop.jpg", "Guests at the bar at Moonshine"),
}

# name -> (index in the sorted ig folder, alt)
IG_PICKS = {
    "ig-dj-vinyl": (6, "A DJ holding a vinyl record in front of shelves of records at Moonshine"),
    "ig-crowd-sing": (7, "Guests singing along at a table at Moonshine, lit red"),
    "ig-crowd-dance": (8, "Guests dancing at Moonshine"),
    "ig-guests-two": (9, "Two guests laughing at the bar at Moonshine"),
    "ig-guest-red": (10, "A guest in a white top posing under red light at Moonshine"),
    "ig-singer-stage": (12, "A singer in a blue sequinned dress on the Moonshine stage"),
    "ig-crowd-red": (13, "A busy table of guests at Moonshine, lit red"),
    "ig-group-sing": (14, "A group of guests singing together at Moonshine"),
    "ig-bar-bulbs": (15, "A bartender at the Moonshine bar under filament bulbs"),
    "ig-bar-guest": (17, "A bartender serving a guest at the Moonshine bar"),
    "ig-band-stage": (18, "A band performing on the Moonshine stage in front of the Moonshine sign"),
    "ig-singer-close": (19, "A singer in a black dress at the microphone at Moonshine"),
    "ig-bar-taps": (20, "A bartender pouring at the brass beer taps at Moonshine"),
    "ig-guitar-stage": (22, "A guitarist performing on the Moonshine stage"),
}

WIDTHS = [(1800, ""), (900, "-900"), (480, "-480")]
manifest = {}


def process(name, src, alt):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    w, h = im.size
    entry = {"w": w, "h": h, "alt": alt, "variants": []}
    made = set()
    for maxw, suffix in WIDTHS:
        target = min(maxw, w)
        if target in made:
            continue
        made.add(target)
        t = im.copy()
        t.thumbnail((target, target * 3))
        t.save(OUT / f"{name}{suffix}.jpg", quality=82, optimize=True, progressive=True)
        t.save(OUT / f"{name}{suffix}.webp", quality=80, method=6)
        entry["variants"].append({"suffix": suffix, "w": t.width, "h": t.height})
    # the un-suffixed file must always exist for the plain <img src>
    if "" not in [v["suffix"] for v in entry["variants"]]:
        im.save(OUT / f"{name}.jpg", quality=82, optimize=True, progressive=True)
        im.save(OUT / f"{name}.webp", quality=80, method=6)
        entry["variants"].insert(0, {"suffix": "", "w": w, "h": h})
    entry["variants"].sort(key=lambda v: v["w"])
    manifest[name] = entry
    print(f"  {name:<22} {w}x{h}  <- {Path(src).name}")


for name, (src, alt) in PICKS.items():
    p = SRC / src
    if p.exists():
        process(name, p, alt)
    else:
        print(f"  MISSING {name}: {src}")

for name, (idx, alt) in IG_PICKS.items():
    if idx < len(IG):
        process(name, IG[idx], alt)
    else:
        print(f"  MISSING {name}: ig index {idx}")

# ---- logo, cream line-art version, favicons, OG default ----
logo_src = SRC / "logo-website.png"
if logo_src.exists():
    logo = Image.open(logo_src).convert("RGBA")
    logo.thumbnail((600, 600))
    logo.save(OUT / "logo.png")
    # cream line-art: keep only the light (gold/cream) marks, drop the dark disc
    g = logo.convert("L")
    a = logo.getchannel("A")
    cream = Image.new("RGBA", logo.size, (242, 232, 213, 0))
    mask = Image.eval(g, lambda v: 255 if v > 95 else 0)
    mask = Image.composite(mask, Image.new("L", logo.size, 0), a)
    cream.putalpha(mask)
    cream.save(OUT / "logo-cream.png")
    for s in (64, 180, 512):
        f = logo.copy()
        f.thumbnail((s, s))
        canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        canvas.paste(f, ((s - f.width) // 2, (s - f.height) // 2), f)
        canvas.save(OUT / f"favicon-{s}.png")
    print("  logo, logo-cream, favicons written")

og_src = SRC / "moonshine-header-img.jpg"
if og_src.exists():
    im = ImageOps.exif_transpose(Image.open(og_src)).convert("RGB")
    og = ImageOps.fit(im, (1200, 630), Image.LANCZOS, centering=(0.5, 0.45))
    og.save(OUT / "og-default.jpg", quality=84, optimize=True)
    print("  og-default.jpg 1200x630 written")

(OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
print(f"manifest: {len(manifest)} images")
