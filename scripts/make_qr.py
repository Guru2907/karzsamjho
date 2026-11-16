"""Make the picture QR for the website and the printed card (D57).

A halftone QR (the method of "Halftone QR codes", Chu et al., SIGGRAPH Asia 2013): the code itself
draws the picture. Every QR module is split into 3x3 small cells. Only the centre cell carries the
data (forced dark or light); the 8 cells around it show the photo, and are only nudged when they
strongly disagree with their module (--dark-max / --light-min). Scanners sample module centres, so
they read the data; the eye sees the photo. Finder squares, timing, alignment and format bits stay
solid. Before that, the photo is cropped to head and shoulders and everything outside a soft oval
is faded to cream: a plain light background is what makes the face readable.

Dev tool only, not part of the API. Needs: pip install segno pillow numpy
Optional check (reads the result back like a phone): pip install zxing-cpp opencv-python-headless

  python scripts/make_qr.py --image photo.png --out web/public/qr-app.png --check

The source photo is a licensed stock image: keep it out of git (docs/assets/*_source.* is ignored).
"""
import argparse

import numpy as np
import segno
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

URL = "https://karzsamjho.vercel.app/app"
INK = (24, 20, 16)          # near-black, the site's foreground
PAPER = (250, 246, 238)     # cream, the site's background
ACCENT = (176, 71, 31)      # burnt orange, the site's primary
QUIET = 4                   # quiet zone in modules (the QR standard asks for 4)
LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def prepare(path, crop, oval=(0.08, -0.02, 0.92, 1.2), contrast=1.35, bright=1.05):
    """Crop, boost, and fade everything outside a soft oval (head and shoulders) to cream."""
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    im = ImageEnhance.Brightness(ImageEnhance.Contrast(im).enhance(contrast)).enhance(bright)
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([oval[0] * w, oval[1] * h, oval[2] * w, oval[3] * h], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(w * 0.05))
    return Image.composite(im, Image.new("RGB", (w, h), PAPER), mask)


def make(photo, out, url=URL, cell=8, dark_max=100, light_min=150):
    """photo: a prepared PIL image. cell: pixels per small cell (a module is 3 cells)."""
    qr = segno.make(url, error="h", boost_error=False)
    n = qr.symbol_size(scale=1, border=0)[0]
    dark = np.array([[bool(v) for v in row] for row in qr.matrix_iter(scale=1, border=0)])
    kinds = [list(row) for row in qr.matrix_iter(scale=1, border=0, verbose=True)]
    k = segno.consts
    fixed = {k.TYPE_FINDER_PATTERN_DARK, k.TYPE_FINDER_PATTERN_LIGHT, k.TYPE_SEPARATOR,
             k.TYPE_TIMING_DARK, k.TYPE_TIMING_LIGHT, k.TYPE_ALIGNMENT_PATTERN_DARK,
             k.TYPE_ALIGNMENT_PATTERN_LIGHT, k.TYPE_FORMAT_DARK, k.TYPE_FORMAT_LIGHT,
             k.TYPE_VERSION_DARK, k.TYPE_VERSION_LIGHT, k.TYPE_DARKMODULE}
    ink, paper = np.array(INK, np.float32), np.array(PAPER, np.float32)
    ink_l, paper_l = float(ink @ LUMA), float(paper @ LUMA)

    cells = np.asarray(photo.resize((3 * n, 3 * n), Image.LANCZOS), dtype=np.float32).copy()
    for r in range(n):
        for c in range(n):
            target = ink if dark[r, c] else paper
            block = cells[3 * r:3 * r + 3, 3 * c:3 * c + 3]
            if kinds[r][c] in fixed:
                block[:] = target
                continue
            for i in range(3):
                for j in range(3):
                    if i == 1 and j == 1:
                        block[i, j] = target          # the data cell
                        continue
                    p = block[i, j]
                    lum = float(p @ LUMA)
                    if dark[r, c] and lum > dark_max:
                        t = (lum - dark_max) / (lum - ink_l)
                        block[i, j] = p * (1 - t) + ink * t
                    elif not dark[r, c] and lum < light_min:
                        t = (light_min - lum) / (paper_l - lum)
                        block[i, j] = p * (1 - t) + paper * t

    body = Image.fromarray(cells.clip(0, 255).astype(np.uint8)).resize((3 * n * cell,) * 2, Image.NEAREST)
    module = 3 * cell
    img = Image.new("RGB", ((n + 2 * QUIET) * module,) * 2, PAPER)
    img.paste(body, (QUIET * module, QUIET * module))
    draw = ImageDraw.Draw(img)
    # Finder squares: orange ring, ink centre. Square corners: rounded finders failed the scan test.
    for fr, fc in ((0, 0), (0, n - 7), (n - 7, 0)):
        x0, y0 = (fc + QUIET) * module, (fr + QUIET) * module
        draw.rectangle([x0, y0, x0 + 7 * module - 1, y0 + 7 * module - 1], fill=ACCENT)
        draw.rectangle([x0 + module, y0 + module, x0 + 6 * module - 1, y0 + 6 * module - 1], fill=PAPER)
        draw.rectangle([x0 + 2 * module, y0 + 2 * module, x0 + 5 * module - 1, y0 + 5 * module - 1], fill=INK)
    img.save(out, optimize=True)
    return img


def check(path, url=URL):
    """Read the QR back at several sizes with ZXing (the engine in many phone scanner apps) and
    OpenCV (stricter). Returns {size: (zxing_ok, opencv_ok)}."""
    import cv2
    import zxingcpp

    img = Image.open(path).convert("RGB")
    results = {}
    for size in (None, 500, 350, 250):
        test = img if size is None else img.resize((size, size), Image.LANCZOS)
        z = url in [b.text for b in zxingcpp.read_barcodes(test)]
        bgr = np.array(test)[:, :, ::-1].copy()
        o = (cv2.QRCodeDetector().detectAndDecode(bgr)[0] or cv2.QRCodeDetectorAruco().detectAndDecode(bgr)[0]) == url
        results["full" if size is None else f"{size}px"] = (z, o)
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--crop", default="30,5,270,245", help="left,top,right,bottom in photo pixels")
    ap.add_argument("--url", default=URL)
    ap.add_argument("--dark-max", type=int, default=100, help="brightest a photo cell in a dark module may be (0-255)")
    ap.add_argument("--light-min", type=int, default=150, help="darkest a photo cell in a light module may be (0-255)")
    ap.add_argument("--check", action="store_true", help="read it back with ZXing and OpenCV")
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    make(prepare(a.image, crop), a.out, a.url, dark_max=a.dark_max, light_min=a.light_min)
    print("wrote", a.out)
    if a.check:
        for size, (z, o) in check(a.out, a.url).items():
            print(f"  {size:5}  ZXing {'OK  ' if z else 'FAIL'}  OpenCV {'OK' if o else 'FAIL'}")


if __name__ == "__main__":
    main()
