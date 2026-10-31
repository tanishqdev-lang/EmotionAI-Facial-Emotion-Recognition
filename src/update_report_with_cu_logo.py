"""
Update PROJECT_REPORT.pdf with the official CU logo images.
ONLY updates the PDF cover page logo — no application code is changed.

Usage:
    py -3.13 src/update_report_with_cu_logo.py
"""

import os
import sys
import shutil
from PIL import Image

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR   = os.path.join(PROJECT_ROOT, "assets")
PDF_OUT      = os.path.join(PROJECT_ROOT, "PROJECT_REPORT.pdf")

# Source logos uploaded by user
CU_LOGO_JPG  = r"D:\Neural Netowrk Projects\Facial-Expression-Recognition-master\data\cu_logo\cu_logos.jpg"
CU_LOGO_PNG  = r"D:\Neural Netowrk Projects\Facial-Expression-Recognition-master\data\cu_logo\cu_logos_2.png"
BANNER_OUT   = os.path.join(ASSETS_DIR, "cu_logo_banner.png")


def build_logo_banner():
    """
    Compose a clean, high-res banner from the user-supplied CU logo files.
    The JPG (201x109) is the primary landscape logo; we scale it up and
    place it on a white canvas that matches the banner slot in the report.
    The PNG variant (166x148) is used as a secondary emblem beside it.
    """
    TARGET_W, TARGET_H = 900, 220   # nice wide banner for the PDF cover

    canvas = Image.new("RGBA", (TARGET_W, TARGET_H), (255, 255, 255, 255))

    # ── Primary logo (JPG) ──────────────────────────────────────────────────
    primary = Image.open(CU_LOGO_JPG).convert("RGBA")
    # Scale to fill ~65 % of banner height
    ratio   = (TARGET_H * 0.85) / primary.height
    new_w   = int(primary.width  * ratio)
    new_h   = int(primary.height * ratio)
    primary = primary.resize((new_w, new_h), Image.LANCZOS)
    # Center the primary logo slightly left of centre
    px = (TARGET_W // 2 - new_w) // 2
    py = (TARGET_H - new_h) // 2
    canvas.paste(primary, (px, py), primary)

    # ── Secondary emblem (PNG) ──────────────────────────────────────────────
    secondary = Image.open(CU_LOGO_PNG).convert("RGBA")
    ratio2    = (TARGET_H * 0.80) / secondary.height
    s_w       = int(secondary.width  * ratio2)
    s_h       = int(secondary.height * ratio2)
    secondary = secondary.resize((s_w, s_h), Image.LANCZOS)
    # Place right of center
    sx = TARGET_W // 2 + (TARGET_W // 2 - s_w) // 2
    sy = (TARGET_H - s_h) // 2
    canvas.paste(secondary, (sx, sy), secondary)

    # Save as high-quality PNG (overwrite the old placeholder banner)
    canvas.save(BANNER_OUT, "PNG", optimize=True)
    print(f"[OK] Logo banner saved  -> {BANNER_OUT}  ({TARGET_W}x{TARGET_H} px)")
    return BANNER_OUT


def regenerate_pdf_only():
    """Import and call only the PDF generator from the existing report script."""
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    parent  = os.path.dirname(src_dir)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    # Import the PDF generator from the existing report module
    from recreate_academic_reports import generate_cu_pdf
    generate_cu_pdf()
    print(f"[OK] PDF regenerated    -> {PDF_OUT}")


if __name__ == "__main__":
    print("=" * 60)
    print("  CU Logo -> PROJECT_REPORT.pdf  (no code changes)")
    print("=" * 60)

    # 1. Validate source logos
    for p in [CU_LOGO_JPG, CU_LOGO_PNG]:
        if not os.path.exists(p):
            print(f"[!] Logo not found: {p}")
            sys.exit(1)

    # 2. Build composite banner
    build_logo_banner()

    # 3. Regenerate only the PDF using the existing academic report generator
    print("\n[->] Regenerating PROJECT_REPORT.pdf with the updated logo...")
    regenerate_pdf_only()

    print("\n[OK] Done — PROJECT_REPORT.pdf updated with official CU logo.")
    print("    No application code was modified.")
