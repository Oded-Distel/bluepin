"""
BluePin – Build standalone HTML for the customer.

תהליך:
  1. רינדור התכניות (מקור + מסומנת) ל-PNG
  2. הזרקת התמונות כ-base64 לתבנית
  3. תפוקה: קובץ HTML יחיד שניתן לשלוח ללקוח

השימוש:
  python3 build_tool.py

קלט נדרש בתיקייה:
  - התמצאות.pdf            (תכנית מקור)
  - תכנית מסומנת WB.pdf    (תכנית עם סימוני יד)
  - marker-tool-template.html  (תבנית עם __ORIG_SRC__ ו-__MARKED_SRC__)

תוצאה:
  - original.png              (תכנית מקור מרונדרת)
  - marked_upright.png        (תכנית מסומנת מסובבת)
  - סימון-וולבוקס.html       (הקובץ ללקוח, ~1.8MB)
"""

import os, io, base64
import fitz
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

ORIG_PDF   = os.path.join(HERE, "התמצאות.pdf")
MARKED_PDF = os.path.join(HERE, "תכנית מסומנת WB.pdf")
TEMPLATE   = os.path.join(HERE, "marker-tool-template.html")
OUT_HTML   = os.path.join(HERE, "סימון-וולבוקס.html")


def render_pdf(pdf_path: str, out_png: str, dpi: int = 300) -> None:
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    doc[0].get_pixmap(matrix=mat).save(out_png)
    doc.close()


def jpeg_b64(img: Image.Image, quality: int) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def main():
    # 1. רינדור התכנית המקורית
    orig_png = os.path.join(HERE, "original.png")
    render_pdf(ORIG_PDF, orig_png)

    # 2. רינדור תכנית מסומנת + סיבוב 180° כדי שטקסט יקרא
    marked_png = os.path.join(HERE, "marked.png")
    render_pdf(MARKED_PDF, marked_png)
    upright = os.path.join(HERE, "marked_upright.png")
    Image.open(marked_png).rotate(180, expand=True).save(upright)

    # 3. הזרקה לתבנית
    orig = Image.open(orig_png)
    orig_b64 = jpeg_b64(orig, quality=92)  # חד – הלקוח לוחץ עליו

    marked = Image.open(upright)
    mw, mh = marked.size
    scale = 1500 / max(mw, mh)
    small = marked.resize((int(mw * scale), int(mh * scale)), Image.LANCZOS)
    marked_b64 = jpeg_b64(small, quality=82)  # להתייחסות בלבד – אפשר נמוך יותר

    with open(TEMPLATE) as f:
        html = f.read()
    html = html.replace("__ORIG_SRC__", f"data:image/jpeg;base64,{orig_b64}")
    html = html.replace("__MARKED_SRC__", f"data:image/jpeg;base64,{marked_b64}")

    with open(OUT_HTML, "w") as f:
        f.write(html)

    size_mb = os.path.getsize(OUT_HTML) / 1024 / 1024
    print(f"✓ {OUT_HTML} ({size_mb:.2f} MB)")
    print("  שלח את הקובץ ללקוח (וואטסאפ/מייל).")
    print("  כשתחזיר ממנו markers.json, הרץ:")
    print("    python3 render_from_json.py markers.json")


if __name__ == "__main__":
    main()
