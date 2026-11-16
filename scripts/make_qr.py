"""Make the picture QR for the website and the printed card (D57).

A "halftone" QR: the photo fills the code at full detail. Each QR module keeps a solid centre dot
that carries the data (dark or light). Around the dot the photo is left alone wherever it already
agrees with the module; only pixels on the wrong side are pushed just past a threshold
(--dark-max / --light-min), so the picture survives and phone scanners still read it. The finder squares, timing
lines, alignment square and format/version bits are drawn solid, because scanners rely on them.

Dev tool only, not part of the API. Needs: pip install segno pillow numpy  (optional check: opencv-python-headless)

  python scripts/make_qr.py --image photo.jpg --crop 15,15,265,265 --out web/public/qr-app.png
  python scripts/make_qr.py ... --check      # read the result back with OpenCV and print the link

The source photo is a licensed stock image: keep it out of git (docs/assets/*_source.* is ignored).
"""
import argparse

import numpy as np
import segno
from PIL import Image, ImageDraw, ImageEnhance

URL = "https://karzsamjho.vercel.app/app"
INK = (24, 20, 16)          # near-black, the site's foreground
PAPER = (250, 246, 238)     # cream, the site's background
ACCENT = (176, 71, 31)      # burnt orange, the site's primary
QUIET = 4                   # quiet zone in modules (the QR standard asks for 4)


def make(image_path, crop, out, url=URL, module=30, dark_max=90, light_min=170, contrast=1.2, dot=0.45):
    qr = segno.make(url, error="h", boost_error=False)
    n = qr.symbol_size(scale=1, border=0)[0]
    side = n * module
    size = (n + 2 * QUIET) * module

    photo = Image.open(image_path).convert("RGB")
    if crop:
        photo = photo.crop(crop)
    photo = ImageEnhance.Contrast(photo).enhance(contrast).resize((side, side), Image.LANCZOS)

    k = segno.consts
    fixed = {k.TYPE_FINDER_PATTERN_DARK, k.TYPE_FINDER_PATTERN_LIGHT, k.TYPE_SEPARATOR,
             k.TYPE_TIMING_DARK, k.TYPE_TIMING_LIGHT, k.TYPE_ALIGNMENT_PATTERN_DARK,
             k.TYPE_ALIGNMENT_PATTERN_LIGHT, k.TYPE_FORMAT_DARK, k.TYPE_FORMAT_LIGHT,
             k.TYPE_VERSION_DARK, k.TYPE_VERSION_LIGHT, k.TYPE_DARKMODULE}
    values = [[bool(v) for v in row] for row in qr.matrix_iter(scale=1, border=0)]
    kinds = [list(row) for row in qr.matrix_iter(scale=1, border=0, verbose=True)]

    # 1. Only fix pixels that disagree with their module: in a dark module, photo pixels lighter
    #    than dark_max are darkened just down to it; in a light module, pixels darker than light_min
    #    are lightened just up to it. Pixels already on the right side are left as the photo.
    a = np.asarray(photo, dtype=np.float32)
    lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    dark_mask = np.kron(np.array(values, dtype=bool), np.ones((module, module), dtype=bool))
    ink, paper = np.array(INK, np.float32), np.array(PAPER, np.float32)
    ink_l, paper_l = float(ink @ [0.299, 0.587, 0.114]), float(paper @ [0.299, 0.587, 0.114])
    to_ink = dark_mask & (lum > dark_max)
    to_paper = ~dark_mask & (lum < light_min)
    t = np.zeros_like(lum)
    t[to_ink] = (lum[to_ink] - dark_max) / (lum[to_ink] - ink_l)
    t[to_paper] = (light_min - lum[to_paper]) / (paper_l - lum[to_paper])
    target = np.where(dark_mask[..., None], ink, paper)
    a = a * (1 - t[..., None]) + target * t[..., None]
    body = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(body)

    # 2. Data modules: a solid centre dot carries the bit.
    pad = round(module * (1 - dot) / 2)
    for r in range(n):
        for c in range(n):
            x0, y0 = c * module, r * module
            colour = INK if values[r][c] else PAPER
            if kinds[r][c] in fixed:
                # 3. Format, version, timing, alignment: solid, scanners rely on them.
                draw.rectangle([x0, y0, x0 + module - 1, y0 + module - 1], fill=colour)
            else:
                draw.rounded_rectangle([x0 + pad, y0 + pad, x0 + module - 1 - pad, y0 + module - 1 - pad],
                                       radius=module * dot / 4, fill=colour)

    # 4. Finder squares: cream separator, orange ring, ink centre. Nearly square: rounded finders fail to scan.
    for fr, fc in ((0, 0), (0, n - 7), (n - 7, 0)):
        x0, y0 = fc * module, fr * module
        draw.rectangle([max(x0 - module, 0), max(y0 - module, 0),
                        min(x0 + 8 * module, side) - 1, min(y0 + 8 * module, side) - 1], fill=PAPER)
        draw.rounded_rectangle([x0, y0, x0 + 7 * module - 1, y0 + 7 * module - 1], radius=module * 0.25, fill=ACCENT)
        draw.rounded_rectangle([x0 + module, y0 + module, x0 + 6 * module - 1, y0 + 6 * module - 1],
                               radius=module * 0.15, fill=PAPER)
        draw.rounded_rectangle([x0 + 2 * module, y0 + 2 * module, x0 + 5 * module - 1, y0 + 5 * module - 1],
                               radius=module * 0.15, fill=INK)

    img = Image.new("RGB", (size, size), PAPER)
    img.paste(body, (QUIET * module, QUIET * module))
    img.save(out, optimize=True)
    return img


def check(path):
    """Read the QR back like a phone would: full size, small, and slightly blurred."""
    import cv2

    img = cv2.imread(path)
    det = cv2.QRCodeDetector()
    aruco = cv2.QRCodeDetectorAruco()
    results = {}
    for name, test in (
        ("full", img),
        ("small 300px", cv2.resize(img, (300, 300), interpolation=cv2.INTER_AREA)),
        ("small 200px", cv2.resize(img, (200, 200), interpolation=cv2.INTER_AREA)),
        ("blurred", cv2.GaussianBlur(cv2.resize(img, (400, 400), interpolation=cv2.INTER_AREA), (3, 3), 0)),
    ):
        text = det.detectAndDecode(test)[0] or aruco.detectAndDecode(test)[0]
        results[name] = text or None
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--crop", help="left,top,right,bottom in photo pixels")
    ap.add_argument("--url", default=URL)
    ap.add_argument("--module", type=int, default=30, help="pixels per QR module")
    ap.add_argument("--dot", type=float, default=0.4, help="data dot size as a share of the module")
    ap.add_argument("--dark-max", type=int, default=90, help="brightest a pixel in a dark module may be (0-255)")
    ap.add_argument("--light-min", type=int, default=170, help="darkest a pixel in a light module may be (0-255)")
    ap.add_argument("--contrast", type=float, default=1.2)
    ap.add_argument("--check", action="store_true", help="read it back with OpenCV")
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    make(a.image, crop, a.out, a.url, a.module, a.dark_max, a.light_min, a.contrast, a.dot)
    print("wrote", a.out)
    if a.check:
        for name, text in check(a.out).items():
            print(f"  {name:12} {'OK  ' if text == a.url else 'FAIL'} {text}")


if __name__ == "__main__":
    main()
