"""
Convert markers.json (exported from marker-tool.html) into the final annotated PDF.

Usage:
    python3 render_from_json.py markers.json

Output:
    תכנית וולבוקס - חדשה.pdf  (and .png)
"""

import sys, os, json
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG_PNG = os.path.join(HERE, "original.png")
FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"
FONT_BOLD_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

def font(sz, bold=False):
    return ImageFont.truetype(FONT_BOLD_PATH if bold else FONT_PATH, sz)

def he(s):
    return get_display(s)


def render(markers_path):
    markers = json.load(open(markers_path, encoding="utf-8"))
    base = Image.open(ORIG_PNG).convert("RGB")
    BW, BH = base.size

    LEGEND_W = 1300
    canvas = Image.new("RGB", (BW + LEGEND_W, BH), "white")
    canvas.paste(base, (0, 0))
    d = ImageDraw.Draw(canvas)

    # Cameras (blue)
    CAM = (0, 90, 220)
    for m in markers:
        if m["type"] != "cam":
            continue
        x, y = int(m["x"]), int(m["y"])
        d.ellipse([x-22, y-22, x+22, y+22], outline=CAM, fill=CAM, width=3)
        if m.get("name"):
            _label(d, m["name"], x+35, y, CAM)

    # WBs (red)
    RED = (190, 20, 20)
    for m in markers:
        if m["type"] != "wb":
            continue
        x, y = int(m["x"]), int(m["y"])
        d.ellipse([x-28, y-28, x+28, y+28], outline=RED, width=6)
        d.ellipse([x-6, y-6, x+6, y+6], fill=RED)
        if m.get("name"):
            _label(d, m["name"], x+35, y, RED)

    _legend(d, BW, 0, LEGEND_W, BH, RED, CAM)

    out_png = os.path.join(HERE, "תכנית וולבוקס - חדשה.png")
    out_pdf = os.path.join(HERE, "תכנית וולבוקס - חדשה.pdf")
    canvas.save(out_png, "PNG", dpi=(300, 300))
    canvas.save(out_pdf, "PDF", resolution=200.0)
    print(f"Saved: {out_png}")
    print(f"Saved: {out_pdf}")


def _label(d, text, x, y, color):
    f = font(36, bold=True)
    t = he(text) if any('֐' <= c <= '׿' for c in text) else text
    bbox = d.textbbox((x, y-22), t, font=f)
    pad = 4
    d.rectangle([bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad], fill="white")
    d.text((x, y-22), t, fill=color, font=f)


def _legend(d, x0, y0, w, h, RED, CAM):
    d.rectangle([x0+20, y0+20, x0+w-20, y0+h-20], outline=(0,0,0), width=3)
    # Title
    title = he("מקרא וולבוקס")
    tf = font(58, bold=True)
    tb = d.textbbox((0,0), title, font=tf)
    d.text((x0 + (w - tb[2]) // 2, y0 + 50), title, fill=RED, font=tf)
    # Keys
    kf = font(32)
    right = x0 + w - 40
    ky = y0 + 170
    d.ellipse([right-40, ky, right, ky+40], outline=RED, width=5)
    d.ellipse([right-26, ky+14, right-14, ky+26], fill=RED)
    t = he("מיקום וולבוקס")
    tb = d.textbbox((0,0), t, font=kf)
    d.text((right - 60 - tb[2], ky+5), t, fill=RED, font=kf)

    ky += 70
    d.ellipse([right-40, ky, right, ky+40], outline=CAM, fill=CAM, width=3)
    t = he("מיקום מצלמה")
    tb = d.textbbox((0,0), t, font=kf)
    d.text((right - 60 - tb[2], ky+5), t, fill=CAM, font=kf)

    d.line([(x0+40, ky+80), (right, ky+80)], fill=(0,0,0), width=2)

    ENTRIES = [
        ("WB MAIN A", "7 * ארון תקשורת 44U (חצר משק)"),
        ("WB A",      "1 * ארון תקשורת 15U (מצלמות ראשיות פלטפורמה)"),
        ("WB B",      "1 * ארון תקשורת 6U (מעבר שחקנים)"),
        ("WB C",      "4 * ארון רצפתי שקוע (פינות פרקט זירה)"),
        ("WB D",      "1 * ארון תקשורת 6U (קיר יציע מתקפל)"),
        ("WB MAIN B", "4 * ארון תקשורת 44U (חדר תקשורת TV מפלס 0:0)"),
        ("WB MAIN C", "1 * ארון תקשורת 44U (חדר תקשורת TV מפלס 16)"),
        ("WB Z",      "1 * ארון תקשורת 6U (חדר תקשורת TV קומה 0)"),
        ("WB M",      "1 * ארון תקשורת 6U (חדר בזק כניסה מהרחוב)"),
        ("WB E",      "1 * צינור ללא ארון (מצלמת BEAUTY)"),
        ("WB P",      "1 * צינור ללא ארון (מצלמת פיקסלוט)"),
        ("WB F",      "1 * ארון תקשורת 6U (תא צפייה / אולפן)"),
        ("WB G",      "1 * ארון תקשורת 6U (הלבשת שחקנים)"),
        ("WB T",      "1 * צינור ללא ארון (מצלמת TOP אמצע מגרש תקרה)"),
        ("WB I",      "1 * ארון תקשורת 6U (עיתונאים)"),
        ("WB H",      "1 * ארון תקשורת 6U (מנוחת שחקנים)"),
        ("WB K",      "1 * ארון תקשורת 15U (פינות פרקט זירה)"),
    ]

    nf = font(30, bold=True)
    ef = font(28)
    y = ky + 110
    for name, desc in ENTRIES:
        nw = d.textbbox((0,0), name, font=nf)[2]
        d.text((right - nw, y), name, fill=RED, font=nf)
        dh = he(desc)
        dw = d.textbbox((0,0), dh, font=ef)[2]
        d.text((right - nw - 30, y+3), "–", fill=(0,0,0), font=ef)
        d.text((right - nw - 45 - dw, y+3), dh, fill=(0,0,0), font=ef)
        y += 78


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 render_from_json.py markers.json")
        sys.exit(1)
    render(sys.argv[1])
