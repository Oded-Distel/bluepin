"""
Generate annotated arena plan with WB (red) and camera (blue) markings + legend.
Based on:
- Original plan: התמצאות.pdf (landscape)
- Marked plan: תכנית מסומנת WB.pdf (handwritten reference)
- Legend: מקרא וולבוקס.docx
- Instructions: הוראות.pdf
"""

from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display
import os

SRC_DIR = "/Users/Oded/Desktop/Cursor projects/kaplan"
WORK_DIR = "/tmp/kaplan_work"
OUT_DIR = SRC_DIR

# ---- Fonts ----
FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"
FONT_BOLD_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD_PATH if bold else FONT_PATH, size)

def he(s):
    """Reverse Hebrew for proper display via PIL."""
    return get_display(s)


# ---- Load original landscape plan ----
ORIG_PNG = os.path.join(WORK_DIR, "original.png")
base = Image.open(ORIG_PNG).convert("RGB")
BW, BH = base.size  # 3508 x 2481
print(f"Base size: {BW}x{BH}")


# ---- Define WB positions on the original plan (pixel coords in base image) ----
# Each entry: name, (x, y), color_role
# WB markers are red, camera markers are blue
WB_POSITIONS = [
    # (name, x, y, optional camera coords [(cx, cy), ...])
    ("WB MAIN A", 3050, 950, []),                        # service yard
    ("WB MAIN B", 1700, 1880, []),                       # TV comm room 0:0
    ("WB MAIN C", 2050, 1880, []),                       # TV comm level 16 (separate from MAIN B)
    ("WB Z",      1850, 1820, []),                       # TV comm floor 0
    ("WB A",      1900, 1180, [(1850, 1180)]),           # main camera platform - east side
    ("WB B",      1450, 1580, []),                       # player passage
    # WB C - 4 floor-recessed at court corners
    ("WB C1",     1230, 1015, [(1230, 1015)]),
    ("WB C2",     1730, 1015, [(1730, 1015)]),
    ("WB C3",     1230, 1410, [(1230, 1410)]),
    ("WB C4",     1730, 1410, [(1730, 1410)]),
    ("WB D",      1110, 1180, []),                       # foldable arena wall (west)
    ("WB K",      1760, 1450, []),                       # court corner (parquet) - SE
    ("WB G",      820,  1820, []),                       # player dressing
    ("WB H",      1080, 1900, []),                       # player rest
    ("WB M",      730,  1920, []),                       # Bezeq entrance from street (redefined nearby)
    ("WB I",      1350, 1680, []),                       # journalists
    ("WB F",      1500, 780,  []),                       # viewing booth / studio
    ("WB E",      1450, 380,  [(1450, 1180)]),           # BEAUTY camera tube; camera over center
    ("WB P",      1560, 1180, [(1500, 1180)]),           # Pixellot mid-court
    ("WB T",      1370, 1180, [(1430, 1230)]),           # TOP ceiling middle
]


# ---- Create the extended canvas (plan on left, legend on right) ----
LEGEND_W = 1300
canvas_w = BW + LEGEND_W
canvas_h = BH
canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
canvas.paste(base, (0, 0))

draw = ImageDraw.Draw(canvas)

# ---- Draw camera markers (BLUE) first so WB markers overlay them ----
CAM_R = 22
CAM_COLOR = (0, 80, 220)
for name, x, y, cams in WB_POSITIONS:
    for cx, cy in cams:
        # Blue filled circle
        draw.ellipse([(cx - CAM_R, cy - CAM_R), (cx + CAM_R, cy + CAM_R)],
                     outline=CAM_COLOR, fill=CAM_COLOR, width=3)


# ---- Draw WB markers (RED) ----
RED = (220, 20, 20)
WB_R = 28
label_font = font(36, bold=True)

# To avoid overlapping labels, offset labels per position
LABEL_OFFSETS = {
    "WB MAIN A": (-220, -10),
    "WB MAIN B": ( 35,  -5),
    "WB MAIN C": ( 35,  -5),
    "WB Z":      ( 35,  -45),
    "WB M":      ( 35,  -5),
    "WB A":      ( 35,  -8),
    "WB B":      ( 35,  -8),
    "WB C1":     (-150, -55),
    "WB C2":     ( 35,  -55),
    "WB C3":     (-150,  30),
    "WB C4":     ( 35,   30),
    "WB D":      (-130, -8),
    "WB K":      ( 35,  20),
    "WB G":      (-115, -10),
    "WB H":      ( 35,  -8),
    "WB M":      (-115, -8),
    "WB I":      ( 35,  -8),
    "WB F":      ( 35,  -8),
    "WB E":      ( 35,  -8),
    "WB P":      ( 35,  -8),
    "WB T":      (-130, -8),
}

for name, x, y, cams in WB_POSITIONS:
    # Red circle outline (WB position is the bold blue circle in marked plan → red)
    draw.ellipse([(x - WB_R, y - WB_R), (x + WB_R, y + WB_R)],
                 outline=RED, fill=None, width=6)
    # small red center dot
    draw.ellipse([(x - 6, y - 6), (x + 6, y + 6)], fill=RED)

    # Label
    ox, oy = LABEL_OFFSETS.get(name, (35, -8))
    # Use clean visible label (WB Cn → "WB C")
    label = "WB C" if name.startswith("WB C") and name != "WB C" else name
    # Small white background behind label for readability
    bbox = draw.textbbox((x + ox, y + oy), label, font=label_font)
    pad = 4
    draw.rectangle([bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad],
                   fill=(255, 255, 255))
    draw.text((x + ox, y + oy), label, fill=RED, font=label_font)


# ---- Draw connection arrow from WB to camera where they differ ----
def dashed_line(draw, p1, p2, fill, width=2, dash_len=14, gap_len=10):
    import math
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1:
        return
    ux, uy = dx / dist, dy / dist
    n = int(dist // (dash_len + gap_len))
    for i in range(n + 1):
        sx = x1 + (dash_len + gap_len) * i * ux
        sy = y1 + (dash_len + gap_len) * i * uy
        ex = sx + dash_len * ux
        ey = sy + dash_len * uy
        if (ex - x1) * ux + (ey - y1) * uy > dist:
            ex, ey = x2, y2
        draw.line([(sx, sy), (ex, ey)], fill=fill, width=width)

for name, x, y, cams in WB_POSITIONS:
    for cx, cy in cams:
        if abs(cx - x) > 50 or abs(cy - y) > 50:
            dashed_line(draw, (x, y), (cx, cy), CAM_COLOR, width=3)


# ---- Build the legend on the right ----
LX = BW + 40          # left edge of legend area
LY = 60               # top edge
LW = LEGEND_W - 80    # width of legend area
right_edge = BW + LEGEND_W - 40

# Legend frame
draw.rectangle([BW + 20, 20, BW + LEGEND_W - 20, BH - 20],
               outline=(0, 0, 0), width=3)

# Title
title_he = he("מקרא וולבוקס")
title_font = font(58, bold=True)
tbbox = draw.textbbox((0, 0), title_he, font=title_font)
tw = tbbox[2] - tbbox[0]
draw.text((BW + (LEGEND_W - tw) // 2, LY), title_he, fill=RED, font=title_font)

# Color key
key_y = LY + 100
key_font = font(32)
# Red WB key
draw.ellipse([(right_edge - 50, key_y), (right_edge - 10, key_y + 40)],
             outline=RED, fill=None, width=5)
draw.ellipse([(right_edge - 36, key_y + 14), (right_edge - 24, key_y + 26)], fill=RED)
key_wb_text = he("מיקום וולבוקס")
kbbox = draw.textbbox((0, 0), key_wb_text, font=key_font)
kw = kbbox[2] - kbbox[0]
draw.text((right_edge - 70 - kw, key_y + 5), key_wb_text, fill=RED, font=key_font)

key_y += 70
draw.ellipse([(right_edge - 50, key_y), (right_edge - 10, key_y + 40)],
             outline=CAM_COLOR, fill=CAM_COLOR, width=3)
key_cam_text = he("מיקום מצלמה")
kbbox = draw.textbbox((0, 0), key_cam_text, font=key_font)
kw = kbbox[2] - kbbox[0]
draw.text((right_edge - 70 - kw, key_y + 5), key_cam_text, fill=CAM_COLOR, font=key_font)


# Separator
sep_y = key_y + 80
draw.line([(BW + 40, sep_y), (right_edge, sep_y)], fill=(0, 0, 0), width=2)

# Legend entries (from the Word document)
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

entry_font = font(28)
name_font = font(30, bold=True)
y = sep_y + 30
row_h = 78
for wb_name, desc in ENTRIES:
    # WB name in RED on the right-ish, description after it (RTL)
    # Construct full line as RTL: name on right, description after dash
    name_w = draw.textbbox((0, 0), wb_name, font=name_font)[2]
    # Draw WB name (English, LTR) at right edge
    draw.text((right_edge - name_w, y), wb_name, fill=RED, font=name_font)

    # Draw description Hebrew to the left of name
    desc_he = he(desc)
    desc_w = draw.textbbox((0, 0), desc_he, font=entry_font)[2]
    dash_x = right_edge - name_w - 10
    draw.text((dash_x - 25, y + 3), "–", fill=(0, 0, 0), font=entry_font)
    draw.text((dash_x - 40 - desc_w, y + 3), desc_he, fill=(0, 0, 0), font=entry_font)

    y += row_h

# ---- Save outputs ----
out_png = os.path.join(OUT_DIR, "תכנית וולבוקס - חדשה.png")
out_pdf = os.path.join(OUT_DIR, "תכנית וולבוקס - חדשה.pdf")
canvas.save(out_png, "PNG", dpi=(300, 300))
print(f"Saved PNG: {out_png}")

# Convert to PDF
canvas.save(out_pdf, "PDF", resolution=200.0)
print(f"Saved PDF: {out_pdf}")
