import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so config imports
import config
"""
Maps a PSE recruitment scores CSV onto a copy of the score-card template,
one slide per PNM.

Usage:
    python3 build_slides.py

Reads:
    TEMPLATE_PATH  - the single-slide score card template
    CSV_PATH       - scores CSV. Column headers are matched loosely (see
                      COLUMN_ALIASES below), so minor renames/typos in the
                      source file won't break this — but if a column
                      genuinely can't be found, the error message will
                      show you the actual headers it saw.
    HEADSHOTS_DIR  - local folder of converted headshots, named <email>.jpg

Writes:
    OUTPUT_PATH    - one slide per PNM, sorted by rank
"""

import copy
import csv
import io
import os
import re
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.oxml.ns import qn
from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass  # HEIC lookups will just fail gracefully via load_headshot_stream's caller

# Paths are set in config.py / .env (DATA_DIR, SLIDES_CSV, HEADSHOTS_DIR).
TEMPLATE_PATH = str(config.SLIDES_TEMPLATE_PATH)
CSV_PATH = str(config.SLIDES_CSV)
HEADSHOTS_DIR = str(config.HEADSHOTS_DIR)
OUTPUT_PATH = str(config.SLIDES_OUTPUT)

# Checked in this order per email. The Apps Script conversion pipeline is
# supposed to normalize everything to .jpg, but if it skipped or failed on
# a particular photo (timeout, unsupported source format, etc.), the raw
# upload sometimes ends up sitting in this folder under its original
# extension instead — this catches those without needing to re-run the
# conversion pipeline first.
HEADSHOT_EXTENSIONS = [".jpg", ".jpeg", ".png", ".heic", ".heif"]

# Shape indices on the template slide (0-indexed, in XML order)
IDX_NAME = 1
IDX_FINAL_SCORE = 3
IDX_SHRUNK_SCORE = 6
IDX_BONUS = 8
IDX_NUM_SCORES = 10
IDX_PERCENTILE = 12
# On the template these are indices 13 (picture) and 14 (app number). Since
# duplicate_slide() skips the picture shape, every duplicated slide's shape
# list is missing that one entry — app number shifts down to index 13.
IDX_APP_NUMBER = 13

# Picture placeholder's position/size on the template, read once and reused
# for every inserted headshot so they all line up identically.
PIC_LEFT = Emu(5715000)
PIC_TOP = Emu(714375)
PIC_WIDTH = Emu(2857500)
PIC_HEIGHT = Emu(3333751)

# Logical field -> acceptable header spellings (normalized: lowercased,
# letters/digits only). Handles typos, renames, and re-saves from Excel
# adding stray characters, so a small header change next semester doesn't
# require editing code — just add another alias here if it ever comes up.
COLUMN_ALIASES = {
    "rank": ["rank"],
    "name": ["name"],
    "email": ["email"],
    "final_score": ["finalscore"],
    "shrunk_score": ["shrunkscore"],
    "bonus": ["bonus"],
    "num_scores": ["interactioncount", "numscores", "numberofscores"],
    "percentile": ["percentile"],
    "app_number": [
        "applicationnumer", "applicationnumber", "appnumber",
        "applicationno", "applicationnum",
    ],
}


def normalize_header(h):
    return re.sub(r"[^a-z0-9]", "", h.lower())


def resolve_columns(fieldnames):
    """Map each logical field name to whatever the actual CSV header is."""
    normalized_to_actual = {normalize_header(h): h for h in fieldnames}
    resolved = {}
    unresolved = []
    for field, aliases in COLUMN_ALIASES.items():
        match = next((normalized_to_actual[a] for a in aliases if a in normalized_to_actual), None)
        if match:
            resolved[field] = match
        else:
            unresolved.append(field)
    if unresolved:
        raise SystemExit(
            "Couldn't find a matching column for: " + ", ".join(unresolved) +
            "\n\nActual headers in your CSV: " + ", ".join(fieldnames) +
            "\n\nAdd the real header text as an alias in COLUMN_ALIASES "
            "near the top of this script, matching it to the right logical "
            "field name, then re-run."
        )
    return resolved


def read_csv_rows(path):
    """Excel exports/re-saves are inconsistent about encoding — try the
    common ones rather than hard-coding one and failing on the others."""
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, newline="", encoding=encoding) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"Could not decode {path} with utf-8-sig, cp1252, or latin-1.")


def duplicate_slide(prs, source_slide):
    """Clone a slide's text shapes (not its picture) onto a new slide using
    the same layout, so formatting/position carry over. python-pptx has no
    built-in slide-duplication, so this copies each shape's XML element
    directly — reliable for text boxes, which carry no external
    relationships. Picture shapes are skipped here and re-added per PNM via
    add_picture(), since a copied <a:blip> would point at a relationship ID
    that doesn't exist on the new slide.
    """
    dest = prs.slides.add_slide(source_slide.slide_layout)

    # add_slide() may pre-populate placeholder shapes from the layout;
    # clear those so we start from a blank canvas.
    for shp in list(dest.shapes):
        shp._element.getparent().remove(shp._element)

    # This template sets its purple fill directly on the slide (not the
    # layout/master), so add_slide() doesn't inherit it — copy it over
    # explicitly. Per the schema, <p:bg> must come before <p:spTree>.
    source_bg = source_slide._element.find(qn("p:cSld")).find(qn("p:bg"))
    if source_bg is not None:
        dest_cSld = dest._element.find(qn("p:cSld"))
        dest_cSld.insert(0, copy.deepcopy(source_bg))

    for shape in source_slide.shapes:
        if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            continue
        new_el = copy.deepcopy(shape._element)
        dest.shapes._spTree.append(new_el)

    return dest


def delete_slide(prs, slide):
    """Remove a slide (and its relationship) from the deck."""
    xml_slides = prs.slides._sldIdLst
    for sld in list(xml_slides):
        if prs.slides._sldIdLst.index(sld) == prs.slides.index(slide):
            rId = sld.get(
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            )
            prs.part.drop_rel(rId)
            xml_slides.remove(sld)
            break


def set_text(slide, idx, value):
    shape = slide.shapes[idx]
    tf = shape.text_frame
    # Assign to the first run to preserve existing font/size/color;
    # tf.text = "..." would collapse formatting to a single default run.
    p = tf.paragraphs[0]
    if p.runs:
        p.runs[0].text = value
        for extra in p.runs[1:]:
            extra.text = ""
    else:
        p.text = value
    return p.runs[0] if p.runs else None


# Rough capacity of the (widened) name value box at the template's base
# font size — calibrated empirically against the actual template render,
# not a real font-metrics calculation. Long names get scaled down from
# there so they stay on one line instead of wrapping into the Final Score
# row beneath them (the template uses fixed y-positions, so a wrapped name
# has nowhere to grow into without a collision).
NAME_BASE_FONT_PT = 20
NAME_BASE_CAPACITY_CHARS = 23
NAME_MIN_FONT_PT = 13


def set_name(slide, idx, name):
    run = set_text(slide, idx, name)
    if run is None:
        return
    if len(name) > NAME_BASE_CAPACITY_CHARS:
        size = max(
            NAME_MIN_FONT_PT,
            int(NAME_BASE_FONT_PT * NAME_BASE_CAPACITY_CHARS / len(name)),
        )
        run.font.size = Pt(size)


def fmt(value, decimals=2):
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def find_headshot_path(headshots_dir, email):
    """Look for <email> under any of the extensions we've actually seen
    show up in this folder, not just .jpg."""
    for ext in HEADSHOT_EXTENSIONS:
        candidate = os.path.join(headshots_dir, f"{email}{ext}")
        if os.path.exists(candidate):
            return candidate
    return None


def load_headshot_stream(path, target_width, target_height):
    """Headshot files are all named/extensioned as .jpg by the conversion
    pipeline, but some phone-camera exports (e.g. MPO — a multi-frame JPEG
    container some cameras use for dual/3D shots) aren't recognized by
    python-pptx even though the file plays fine everywhere else and the
    extension says .jpg. Decode with Pillow and re-encode as a plain
    single-frame JPEG in memory, so add_picture() always gets a format it
    understands regardless of what the source file actually is under the
    hood.

    Two more fixes happen here:

    - EXIF rotation: phones often store "this photo is rotated 90°" as
      metadata rather than actually rotating the pixels, and apps like
      Photos/Preview quietly rotate on display using that tag. Re-encoding
      without reading it first bakes in the sideways version permanently.
      exif_transpose() applies the rotation to the actual pixels before we
      save, so it's upright everywhere from here on, tag or no tag.

    - Aspect-ratio crop: add_picture() with an explicit width AND height
      stretches the image to exactly fill that box, regardless of the
      photo's real proportions — that's what was warping faces. Instead,
      crop (not squish) each photo to the placeholder's exact aspect ratio
      before handing it to add_picture, the same way a phone's contact
      photo or a LinkedIn avatar crops to fit a fixed frame.
    """
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    target_ratio = target_width / target_height
    w, h = img.size
    src_ratio = w / h

    if src_ratio > target_ratio:
        # Photo is relatively wider than the frame — crop the sides.
        new_w = round(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # Photo is relatively taller than the frame — crop top/bottom.
        new_h = round(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf


def main():
    prs = Presentation(TEMPLATE_PATH)
    template_slide = prs.slides[0]

    # Template bug: the "Name :" label box (index 0) is too narrow for its
    # own text at 20pt bold, so it wraps to two lines and overlaps the
    # "Final Score:" row beneath it on every slide. Widen it once, before
    # duplicating, since there's clear space before the value column.
    template_slide.shapes[0].width = Emu(1600000)

    # Same category of bug, other side of the row: the Name *value* box
    # (index 1) is only 3.125in wide, so long names (e.g. a full name with a
    # nickname in parentheses, or three-part surnames) wrap onto a second line and collide
    # with Final Score beneath. Widen it as far as it can go before
    # touching the headshot (which starts at x=6.25in) — set_name() handles
    # the remaining, longer outliers by shrinking their font.
    template_slide.shapes[1].width = Emu(3300000)

    # Belt-and-suspenders for the same issue: font metrics for "Oswald"
    # may render slightly differently on your machine than in this sandbox
    # (font substitution is common when a font isn't installed), so the
    # shrink-to-fit above isn't guaranteed precise. Permanently shift every
    # row from Final Score down by one line's worth of space, so a name
    # that wraps to two lines has guaranteed room regardless of exact
    # wrap point. There's ample blank space at the bottom of the card to
    # absorb this.
    ROW_SHIFT = Emu(400000)
    for i in range(2, 13):
        shape = template_slide.shapes[i]
        shape.top = Emu(shape.top + ROW_SHIFT)

    rows = read_csv_rows(CSV_PATH)
    if not rows:
        raise SystemExit(f"{CSV_PATH} has no data rows.")

    col = resolve_columns(rows[0].keys())
    rows.sort(key=lambda r: int(r[col["rank"]]))

    missing_headshots = []
    broken_headshots = []

    for row in rows:
        slide = duplicate_slide(prs, template_slide)

        set_name(slide, IDX_NAME, row[col["name"]])
        set_text(slide, IDX_FINAL_SCORE, fmt(row[col["final_score"]]))
        set_text(slide, IDX_SHRUNK_SCORE, fmt(row[col["shrunk_score"]]))
        set_text(slide, IDX_BONUS, fmt(row[col["bonus"]]))
        set_text(slide, IDX_NUM_SCORES, str(int(float(row[col["num_scores"]]))))
        set_text(slide, IDX_PERCENTILE, fmt(row[col["percentile"]], decimals=1))
        set_text(slide, IDX_APP_NUMBER, str(row[col["app_number"]]).strip())

        name = row[col["name"]]
        email = row[col["email"]].strip().lower()
        headshot_path = find_headshot_path(HEADSHOTS_DIR, email)

        if headshot_path:
            try:
                image_stream = load_headshot_stream(headshot_path, PIC_WIDTH, PIC_HEIGHT)
                slide.shapes.add_picture(
                    image_stream, PIC_LEFT, PIC_TOP, PIC_WIDTH, PIC_HEIGHT
                )
            except Exception as e:
                broken_headshots.append(f"{name} ({e})")
        else:
            missing_headshots.append(name)

    # Remove the original sample slide now that every PNM has
    # their own slide.
    delete_slide(prs, template_slide)

    prs.save(OUTPUT_PATH)

    print(f"Wrote {len(rows)} slides to {OUTPUT_PATH}")
    if missing_headshots:
        print(f"\nNo headshot file found for {len(missing_headshots)} PNMs:")
        for name in missing_headshots:
            print(f"  - {name}")
    if broken_headshots:
        print(f"\nHeadshot file existed but couldn't be read for {len(broken_headshots)} PNMs:")
        for entry in broken_headshots:
            print(f"  - {entry}")


if __name__ == "__main__":
    main()
