"""
גרסת "שינוי פרופורציות" - מקרא צר וקטן יותר, שרטוט תופס יותר מקום.
פלט: תכנית וולבוקס - שינוי פרופורציות.pdf / .png

Usage:
    python3 render_proportions.py markers.json
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

    # פרופורציות חדשות: המקרא צומצם מ-1300 ל-820 פיקסלים
    # התוצאה: השרטוט תופס ~81% מהרוחב (במקום 73%)
    LEGEND_W = 820
    canvas = Image.new("RGB", (BW + LEGEND_W, BH), "white")
    canvas.paste(base, (0, 0))
    d = ImageDraw.Draw(canvas)

    CAM = (0, 90, 220)
    for m in markers:
        if m["type"] != "cam":
            continue
        x, y = int(m["x"]), int(m["y"])
        d.ellipse([x-22, y-22, x+22, y+22], outline=CAM, fill=CAM, width=3)
        if m.get("name"):
            _label(d, m["name"], x+35, y, CAM)

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

    out_png = os.path.join(HERE, "תכנית וולבוקס - שינוי פרופורציות.png")
    out_pdf = os.path.join(HERE, "תכנית וולבוקס - שינוי פרופורציות.pdf")
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
    d.rectangle([x0+15, y0+15, x0+w-15, y0+h-15], outline=(0,0,0), width=3)

    # כותרת - הוקטנה מ-58 ל-42
    title = he("מקרא וולבוקס")
    tf = font(42, bold=True)
    tb = d.textbbox((0,0), title, font=tf)
    d.text((x0 + (w - tb[2]) // 2, y0 + 35), title, fill=RED, font=tf)

    # מקשים - הוקטנו מ-32 ל-24
    kf = font(24)
    right = x0 + w - 30
    ky = y0 + 120
    d.ellipse([right-30, ky, right, ky+30], outline=RED, width=4)
    d.ellipse([right-20, ky+10, right-10, ky+20], fill=RED)
    t = he("מיקום וולבוקס")
    tb = d.textbbox((0,0), t, font=kf)
    d.text((right - 45 - tb[2], ky+2), t, fill=RED, font=kf)

    ky += 50
    d.ellipse([right-30, ky, right, ky+30], outline=CAM, fill=CAM, width=3)
    t = he("מיקום מצלמה")
    tb = d.textbbox((0,0), t, font=kf)
    d.text((right - 45 - tb[2], ky+2), t, fill=CAM, font=kf)

    d.line([(x0+30, ky+60), (right, ky+60)], fill=(0,0,0), width=2)

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

    # שמות - הוקטנו מ-30 ל-22, תיאורים מ-28 ל-20, רווח מ-78 ל-58
    nf = font(22, bold=True)
    ef = font(20)
    y = ky + 85
    for name, desc in ENTRIES:
        nw = d.textbbox((0,0), name, font=nf)[2]
        d.text((right - nw, y), name, fill=RED, font=nf)
        dh = he(desc)
        dw = d.textbbox((0,0), dh, font=ef)[2]
        d.text((right - nw - 20, y+2), "–", fill=(0,0,0), font=ef)
        d.text((right - nw - 35 - dw, y+2), dh, fill=(0,0,0), font=ef)
        y += 58


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 render_proportions.py markers.json")
        sys.exit(1)
    render(sys.argv[1])
