"""Draw the demo-pack images (G1, D52) from api/data/offers/demo_pack.json.

    python scripts/make_demo_pack.py            -> api/data/offers/demo/01.png ... 10.png

Rules (docs/progress/2026-11-14_0500_G-demo-pack_siddeshwar.md):
- Every word on an image comes from that item's "text_on_image" list, and every line of the list is
  drawn (the script stops otherwise). Long lines wrap; the words stay exactly the same.
- Drawn by code, never by an image AI, so every digit is exact.
- Hindi (Devanagari) and Bengali need text shaping (vowel signs, joined letters). This Pillow has no
  libraqm, so text is shaped with HarfBuzz (uharfbuzz) and drawn glyph by glyph with FreeType
  (freetype-py). The script stops if any character has no glyph (it would print as an empty box).
- No logos, no brand colours of a real company, no extra text (no clock, no app names).
- The same input gives the same files.

Needs, locally only (NOT in api/requirements.txt): pip install pillow uharfbuzz freetype-py
Fonts (Windows): C:\\Windows\\Fonts\\segoeui.ttf, segoeuib.ttf (English), Nirmala.ttc (Hindi, Bengali).
"""
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

import freetype
import uharfbuzz as hb
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "api" / "data" / "offers" / "demo_pack.json"
OUT = ROOT / "api" / "data" / "offers" / "demo"
FONTS = Path("C:/Windows/Fonts")
W = 1080                                   # portrait, 1080 px wide
INDIC = re.compile(r"[\u0900-\u097F\u0980-\u09FF]")
TICK = "✅"                                # drawn as an icon: no font here has it


# ---------------------------------------------------------------- text: shape + draw
@lru_cache(maxsize=None)
def _faces(bold: bool, indic: bool):
    """(HarfBuzz font, FreeType face path, index) for one style."""
    if indic:
        path, index = str(FONTS / "Nirmala.ttc"), (1 if bold else 0)
    else:
        path, index = str(FONTS / ("segoeuib.ttf" if bold else "segoeui.ttf")), 0
    blob = hb.Blob.from_file_path(path)
    return hb.Font(hb.Face(blob, index)), path, index


@lru_cache(maxsize=None)
def _ft(path: str, index: int, size: int):
    face = freetype.Face(path, index)
    face.set_pixel_sizes(0, size)
    return face


def shape(text: str, size: int, bold: bool):
    """-> (glyphs [(gid, x, y_offset)], width px). Stops on a missing glyph (an empty box)."""
    indic = bool(INDIC.search(text))
    font, path, index = _faces(bold, indic)
    font.scale = (size * 64, size * 64)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    glyphs, pen = [], 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        if info.codepoint == 0:
            raise SystemExit(f"missing glyph (would print as a box) in {text!r} with {Path(path).name}")
        glyphs.append((info.codepoint, pen + pos.x_offset / 64, pos.y_offset / 64))
        pen += pos.x_advance / 64
    return glyphs, pen, (path, index)


def width(text: str, size: int, bold: bool = False) -> float:
    return shape(text, size, bold)[1]


def draw_text(img: Image.Image, xy, text: str, size: int, color, bold: bool = False) -> float:
    """Draw one line with its top-left at xy; returns the width drawn."""
    glyphs, total, (path, index) = shape(text, size, bold)
    face = _ft(path, index, size)
    x0, y0 = xy
    baseline = y0 + round(size * 0.95)
    layer = Image.new("L", img.size, 0)
    for gid, gx, gy in glyphs:
        face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
        g = face.glyph
        bm = g.bitmap
        if bm.width == 0 or bm.rows == 0:
            continue
        mask = Image.frombytes("L", (bm.width, bm.rows), bytes(bm.buffer), "raw", "L", bm.pitch)
        px = round(x0 + gx + g.bitmap_left)
        py = round(baseline - gy - g.bitmap_top)
        _max_paste(layer, mask, (px, py))
    solid = Image.new("RGB", img.size, color)
    img.paste(solid, (0, 0), layer)
    return total


def _max_paste(layer: Image.Image, mask: Image.Image, at) -> None:
    """Merge a glyph into the text layer (keeps overlapping glyph edges smooth)."""
    from PIL import ImageChops
    region = (at[0], at[1], at[0] + mask.width, at[1] + mask.height)
    current = layer.crop(region)
    layer.paste(ImageChops.lighter(current, mask), region[:2])


def wrap(text: str, size: int, max_w: int, bold: bool = False) -> list[str]:
    """Greedy word wrap; the words are never changed."""
    lines, line = [], ""
    for word in text.split(" "):
        trial = f"{line} {word}" if line else word
        if line and width(trial, size, bold) > max_w:
            lines.append(line)
            line = word
        else:
            line = trial
    lines.append(line)
    return lines


def block(img, x, y, text, size, color, max_w, bold=False, gap=1.32, align="left") -> int:
    """Wrapped paragraph; returns the y below it."""
    for part in wrap(text, size, max_w, bold):
        dx = 0
        if align == "center":
            dx = (max_w - width(part, size, bold)) / 2
        draw_text(img, (x + dx, y), part, size, color, bold)
        y += round(size * gap)
    return y


def block_height(text, size, max_w, bold=False, gap=1.32) -> int:
    return len(wrap(text, size, max_w, bold)) * round(size * gap)


# ---------------------------------------------------------------- small drawing helpers
def rbox(d: ImageDraw.ImageDraw, box, r, fill, outline=None, width=0):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def tick_icon(d: ImageDraw.ImageDraw, x, y, s):
    """The ✅ emoji as a drawn icon: green rounded square, white tick."""
    d.rounded_rectangle((x, y, x + s, y + s), radius=s // 5, fill=(46, 160, 67))
    d.line([(x + s * 0.24, y + s * 0.52), (x + s * 0.43, y + s * 0.72), (x + s * 0.78, y + s * 0.30)],
           fill="white", width=max(4, s // 9), joint="curve")


def sample_stamp(img, d, text, y, color=(150, 40, 40)):
    """'Synthetic sample' stamp, centred, boxed."""
    size = 34
    w = width(text, size, True)
    x = (W - w) / 2
    rbox(d, (x - 24, y - 10, x + w + 24, y + size + 22), 10, None, outline=color, width=3)
    draw_text(img, (x, y), text, size, color, True)


class Lines:
    """Hands out text_on_image lines by index and checks at the end that every line was drawn."""
    def __init__(self, item):
        self.items, self.used, self.id = item["text_on_image"], set(), item["id"]

    def __getitem__(self, i):
        self.used.add(i)
        return self.items[i]

    def check(self):
        missing = set(range(len(self.items))) - self.used
        if missing:
            raise SystemExit(f"{self.id}: lines not drawn: {[self.items[i] for i in sorted(missing)]}")


def phone_frame(h, bg=(236, 239, 243)):
    """A plain phone screen: dark bezel, light screen. No clock or app text."""
    img = Image.new("RGB", (W, h), (24, 26, 30))
    d = ImageDraw.Draw(img)
    rbox(d, (40, 40, W - 40, h - 40), 56, bg)
    d.rounded_rectangle((W // 2 - 90, 58, W // 2 + 90, 78), radius=10, fill=(24, 26, 30))   # speaker slot
    return img, d


# ---------------------------------------------------------------- designs
def sms(item, accent=(52, 120, 246)):
    """Phone SMS screenshot: sender header, date chip, one grey bubble, sample stamp.
    text_on_image: [sender, time, message lines..., 'Synthetic sample']."""
    L = Lines(item)
    body = [L[i] for i in range(2, len(item["text_on_image"]) - 1)]
    size, inner = 54, 780
    bubble_h = sum(block_height(t, size, inner) + 18 for t in body) + 60
    h = 390 + bubble_h + 90 + 70 + 120            # fits the content: bubble, stamp, bezel
    img, d = phone_frame(h)
    # header bar: back chevron, avatar circle with the first letter shape, sender ID
    d.rectangle((40, 96, W - 40, 250), fill=(250, 251, 253))
    d.line([(90, 150), (70, 172), (90, 194)], fill=accent, width=7)
    d.ellipse((120, 128, 210, 218), fill=accent)
    d.ellipse((150, 146, 180, 176), fill=(250, 251, 253))
    d.pieslice((138, 178, 192, 232), 180, 360, fill=(250, 251, 253))
    draw_text(img, (236, 140), L[0], 50, (20, 22, 26), True)
    # date / time chip
    t = L[1]
    tw = width(t, 32)
    rbox(d, ((W - tw) / 2 - 24, 292, (W + tw) / 2 + 24, 348), 28, (222, 226, 232))
    draw_text(img, ((W - tw) / 2, 298), t, 32, (80, 86, 96))
    # bubble
    x, y = 90, 390
    rbox(d, (x, y, x + inner + 80, y + bubble_h), 40, (255, 255, 255), outline=(214, 219, 226), width=2)
    d.polygon([(x + 6, y + bubble_h - 50), (x - 22, y + bubble_h + 6), (x + 50, y + bubble_h - 10)],
              fill=(255, 255, 255))
    ty = y + 34
    for line in body:
        ty = block(img, x + 40, ty, line, size, (18, 20, 24), inner) + 18
    sample_stamp(img, d, L[len(item["text_on_image"]) - 1], y + bubble_h + 90)
    L.check()
    return img


def app_ad(item):
    """Glossy app ad (invented brand, own colours): brand block, big offer card, CTA bar."""
    L = Lines(item)
    rows = [(L[2], 76, (16, 64, 84)), (L[3], 58, (196, 54, 40)), (L[4], 76, (16, 64, 84))]
    card_h = 60 + sum(block_height(t, s, 860, True) + 60 for t, s, _ in rows)
    h = 350 + card_h + 50 + 130 + 90 + 70 + 70
    img = Image.new("RGB", (W, h), (16, 64, 84))
    d = ImageDraw.Draw(img)
    for i in range(0, 2 * h, 6):                               # soft diagonal stripes (no gradient)
        if (i // 6) % 9 == 0:
            d.line([(0, i), (i, 0)], fill=(20, 74, 96), width=3)
    rbox(d, (60, 60, W - 60, 300), 48, (255, 196, 61))
    d.ellipse((100, 110, 240, 250), fill=(16, 64, 84))         # coin icon (invented brand)
    d.ellipse((140, 150, 200, 210), fill=(255, 196, 61))
    draw_text(img, (270, 112), L[0], 84, (16, 40, 52), True)
    block(img, 270, 214, L[1], 40, (40, 52, 60), 700)
    rbox(d, (60, 350, W - 60, 350 + card_h), 48, (255, 255, 255))
    y = 410
    for i, (text, size, color) in enumerate(rows):
        if i:
            d.line([(110, y - 30), (W - 110, y - 30)], fill=(225, 230, 235), width=3)
        y = block(img, 110, y, text, size, color, 860, True) + 60
    cta = 350 + card_h + 50
    rbox(d, (60, cta, W - 60, cta + 130), 65, (255, 196, 61))
    tw = width(L[5], 48, True)
    draw_text(img, ((W - tw) / 2, cta + 36), L[5], 48, (16, 40, 52), True)
    sample_stamp(img, d, L[6], cta + 220, color=(255, 230, 160))
    L.check()
    return img


def whatsapp(item):
    """WhatsApp-style forward: 'Forwarded' label, green bubble, tick icon, time in the bubble."""
    L = Lines(item)
    x, y, inner, size = 90, 200, 800, 54
    texts = [L[2], L[3], L[4], L[5]]
    body_h = sum(block_height(t, size, inner, True) + 22 for t in texts)
    bubble_h = 70 + 80 + body_h + 90
    h = y + bubble_h + 120 + 70 + 120              # fits the content
    img, d = phone_frame(h, bg=(236, 229, 221))
    for yy in range(140, h - 80, 90):                          # faint wallpaper dots
        for xx in range(110, W - 80, 90):
            d.ellipse((xx, yy, xx + 6, yy + 6), fill=(226, 218, 208))
    rbox(d, (x, y, x + inner + 80, y + bubble_h), 36, (220, 248, 198))
    # "Forwarded" label with a small arrow
    d.line([(x + 40, y + 52), (x + 72, y + 52)], fill=(120, 130, 120), width=5)
    d.polygon([(x + 70, y + 40), (x + 86, y + 52), (x + 70, y + 64)], fill=(120, 130, 120))
    draw_text(img, (x + 100, y + 30), L[0], 36, (110, 120, 110))
    # "Loan APPROVED ✅": the words, then the drawn tick icon
    head = L[1]
    words = head.replace(TICK, "").rstrip()
    hw = draw_text(img, (x + 40, y + 96), words, 56, (20, 60, 30), True)
    tick_icon(d, int(x + 40 + hw + 18), y + 104, 56)
    ty = y + 190
    for t in texts:
        ty = block(img, x + 40, ty, t, size, (24, 28, 24), inner, True) + 22
    tw = width(L[6], 30)
    draw_text(img, (x + inner + 40 - tw, y + bubble_h - 56), L[6], 30, (100, 110, 100))
    d.line([(x + inner + 50, y + bubble_h - 38), (x + inner + 58, y + bubble_h - 30),
            (x + inner + 70, y + bubble_h - 46)], fill=(52, 150, 230), width=4)
    sample_stamp(img, d, L[7], y + bubble_h + 120)
    L.check()
    return img


def pamphlet(item):
    """Printed Hindi pamphlet: yellow paper, red headline band, boxed offer, dashed tear-off strip."""
    L = Lines(item)
    h = 1600
    img = Image.new("RGB", (W, h), (255, 240, 150))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 260), fill=(200, 30, 40))
    tw = width(L[0], 110, True)
    draw_text(img, ((W - tw) / 2, 60), L[0], 110, (255, 255, 255), True)
    rbox(d, (70, 320, W - 70, 620), 30, (255, 255, 255), outline=(200, 30, 40), width=8)
    tw = width(L[1], 120, True)
    draw_text(img, ((W - tw) / 2, 380), L[1], 120, (200, 30, 40), True)
    tw = width(L[2], 64, True)
    draw_text(img, ((W - tw) / 2, 690), L[2], 64, (30, 30, 30), True)
    rbox(d, (70, 820, W - 70, 1000), 30, (30, 30, 30))
    tw = width(L[3], 80, True)
    draw_text(img, ((W - tw) / 2, 858), L[3], 80, (255, 240, 150), True)
    tw = width(L[4], 70, True)
    draw_text(img, ((W - tw) / 2, 1070), L[4], 70, (30, 30, 30), True)
    for xx in range(40, W - 40, 40):                           # tear-off strip
        d.line([(xx, 1240), (xx + 20, 1240)], fill=(120, 100, 40), width=4)
    tab = L[0]                                                 # the lender's name, as on real tear-offs
    tab_size = 30
    while width(tab, tab_size, True) > 136 and tab_size > 18:
        tab_size -= 1
    for i in range(5):                                         # 5 tear-off slips, centred, name in each
        cx = 105 + i * 180
        d.rectangle((cx, 1270, cx + 150, 1400), outline=(120, 100, 40), width=3)
        tw = width(tab, tab_size, True)
        draw_text(img, (cx + (150 - tw) / 2, 1312), tab, tab_size, (120, 30, 30), True)
    sample_stamp(img, d, L[5], 1470)
    L.check()
    return img


def email(item):
    """Bank-style email in a mail window (invented lender, own colours): header rows, letter, terms table."""
    L = Lines(item)
    top = (160 + block_height(L[0], 36, 900) + 6 + block_height(L[1], 42, 900, True) + 24 + 180
           + block_height(L[3], 44, 900) + 14 + block_height(L[4], 48, 900, True) + 40)
    h = top + 4 * 110 + 110 + 70 + 110                         # fits the content
    img = Image.new("RGB", (W, h), (226, 230, 236))
    d = ImageDraw.Draw(img)
    rbox(d, (40, 40, W - 40, h - 40), 24, (255, 255, 255), outline=(200, 206, 214), width=2)
    d.rectangle((41, 41, W - 41, 120), fill=(242, 244, 247))
    for i, c in enumerate([(236, 106, 94), (245, 191, 79), (98, 197, 84)]):
        d.ellipse((80 + i * 46, 66, 108 + i * 46, 94), fill=c)
    y = 160
    y = block(img, 90, y, L[0], 36, (70, 76, 86), 900) + 6
    y = block(img, 90, y, L[1], 42, (20, 24, 30), 900, True) + 24
    d.line([(90, y), (W - 90, y)], fill=(220, 224, 230), width=3)
    d.rectangle((90, y + 40, 110, y + 130), fill=(122, 66, 30))          # lender mark: plain bar
    draw_text(img, (136, y + 50), L[2], 60, (122, 66, 30), True)
    y += 180
    y = block(img, 90, y, L[3], 44, (30, 34, 40), 900) + 14
    y = block(img, 90, y, L[4], 48, (30, 34, 40), 900, True) + 40
    rows = [L[5], L[6], L[7], L[8]]
    for i, row in enumerate(rows):
        fill = (246, 240, 232) if i % 2 == 0 else (255, 255, 255)
        d.rectangle((90, y, W - 90, y + 110), fill=fill, outline=(226, 214, 200))
        draw_text(img, (120, y + 28), row, 52, (40, 30, 20), True)
        y += 110
    sample_stamp(img, d, L[9], y + 110)
    L.check()
    return img


def flyer(item):
    """Flyer-style ad whose numbers contradict each other: cream poster, orange boxes."""
    L = Lines(item)
    h = 320 + 3 * 210 + 320 + 70 + 110                         # fits the content
    img = Image.new("RGB", (W, h), (255, 248, 236))
    d = ImageDraw.Draw(img)
    rbox(d, (50, 50, W - 50, 250), 40, (232, 98, 32))
    tw = width(L[0], 96, True)
    draw_text(img, ((W - tw) / 2, 92), L[0], 96, (255, 255, 255), True)
    y = 320
    for i, idx in enumerate((1, 2, 3)):
        rbox(d, (90, y, W - 90, y + 170), 30, (255, 255, 255), outline=(232, 98, 32), width=5)
        tw = width(L[idx], 74, True)
        draw_text(img, ((W - tw) / 2, y + 42), L[idx], 74, (40, 30, 20), True)
        y += 210
    rbox(d, (90, y + 20, W - 90, y + 200), 30, (40, 30, 20))
    tw = width(L[4], 68, True)
    draw_text(img, ((W - tw) / 2, y + 68), L[4], 68, (255, 248, 236), True)
    sample_stamp(img, d, L[5], y + 320)
    L.check()
    return img


def notice(item):
    """Plain neutral notice card (real company: no logo, no brand colours, grey only)."""
    L = Lines(item)
    end = (170 + block_height(L[0], 64, 840, True) + 40 + 50 + block_height(L[1], 60, 840) + 30
           + block_height(L[2], 60, 840) + 60)
    h = end + 80 + 70 + 130                                    # fits the content
    img = Image.new("RGB", (W, h), (238, 238, 238))
    d = ImageDraw.Draw(img)
    rbox(d, (60, 60, W - 60, h - 60), 30, (255, 255, 255), outline=(190, 190, 190), width=3)
    y = 170
    y = block(img, 120, y, L[0], 64, (30, 30, 30), 840, True) + 40
    d.line([(120, y), (W - 120, y)], fill=(210, 210, 210), width=3)
    y = block(img, 120, y + 50, L[1], 60, (30, 30, 30), 840) + 30
    y = block(img, 120, y, L[2], 60, (30, 30, 30), 840) + 60
    sample_stamp(img, d, L[3], y + 80, color=(110, 110, 110))
    L.check()
    return img


# 10 is a real company on RBI's cancelled list: same neutral grey phone frame as 08, sender "Sample SMS"
# (not the company name: the warning needs the exact name, read from the message itself).
DESIGNS = {"01": sms, "02": app_ad, "03": whatsapp, "04": pamphlet, "05": sms, "06": email,
           "07": flyer, "08": lambda it: sms(it, accent=(110, 116, 126)), "09": sms,
           "10": lambda it: sms(it, accent=(110, 116, 126))}


def main() -> None:
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for item in pack["items"]:
        img = DESIGNS[item["id"]](item)
        path = ROOT / "api" / "data" / "offers" / item["file"]
        img.save(path, "PNG", optimize=True)
        print(f"{item['id']}: {path.relative_to(ROOT)} {img.size[0]}x{img.size[1]}")


if __name__ == "__main__":
    sys.exit(main())
