"""Vẽ ảnh nền trang (sidebar, logo, menu, khung KPI) bằng Pillow.

Ảnh xuất ở độ phân giải gấp đôi canvas (3200x1800) để hiển thị sắc nét.
Cần font Segoe UI và Segoe Fluent Icons (lấy từ C:\\Windows\\Fonts).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from layout import (BG, KPI_H, KPI_W, KPI_X, KPI_Y, LIME, NAV, NAV_H, NAV_STEP, NAV_Y, PAGE_H, PAGE_W, PANEL,
                    SIDEBAR, SIDEBAR_W)

S = 2  # hệ số phóng


class Fonts:
    def __init__(self, folder):
        f = Path(folder)
        self.path = {"regular": f / "segoeui.ttf", "semibold": f / "seguisb.ttf", "bold": f / "segoeuib.ttf",
                     "black": f / "seguibl.ttf", "icons": f / "SegoeIcons.ttf"}
        missing = [str(p) for p in self.path.values() if not p.exists()]
        if missing:
            raise SystemExit("Thiếu font: " + ", ".join(missing))

    def __call__(self, kind, size):
        return ImageFont.truetype(str(self.path[kind]), int(size * S))


def spaced_text(d, xy, text, font, fill, spacing):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + spacing * S


def draw_page(path, fonts, active_index, kpi_icons):
    im = Image.new("RGB", (PAGE_W * S, PAGE_H * S), BG)
    d = ImageDraw.Draw(im)

    # Sidebar
    d.rectangle([0, 0, SIDEBAR_W * S, PAGE_H * S], fill=SIDEBAR)
    d.rectangle([SIDEBAR_W * S, 0, SIDEBAR_W * S + S, PAGE_H * S], fill="#262626")
    d.text((26 * S, 18 * S), "OLIST", font=fonts("black", 44), fill=LIME)
    spaced_text(d, (28 * S, 82 * S), "E-COMMERCE ANALYTICS", fonts("semibold", 10.5), "#D9D9D9", 1.6)

    for i, (label, glyph, _) in enumerate(NAV):
        y = NAV_Y + i * NAV_STEP
        active = i == active_index
        if active:
            d.rounded_rectangle([14 * S, y * S, (SIDEBAR_W - 14) * S, (y + NAV_H) * S], radius=12 * S, fill=LIME)
        fg_icon = "#0E0E0E" if active else "#BFBFBF"
        fg_text = "#0E0E0E" if active else "#E0E0E0"
        icon_font = fonts("icons", 21)
        d.text((30 * S, (y + NAV_H / 2) * S), glyph, font=icon_font, fill=fg_icon, anchor="lm")
        d.text((66 * S, (y + NAV_H / 2) * S), label, font=fonts("semibold" if active else "regular", 15),
               fill=fg_text, anchor="lm")

    foot = fonts("regular", 10.5)
    d.text((26 * S, 826 * S), "Source: Olist Brazilian", font=foot, fill="#7A7A7A")
    d.text((26 * S, 843 * S), "E-Commerce Public Dataset", font=foot, fill="#7A7A7A")
    d.text((26 * S, 860 * S), "Scope: Jan 2017 – Aug 2018", font=foot, fill="#7A7A7A")

    # Khung KPI + icon
    for k, glyph in enumerate(kpi_icons):
        x, y = KPI_X[k], KPI_Y
        d.rounded_rectangle([x * S, y * S, (x + KPI_W) * S, (y + KPI_H) * S], radius=14 * S, fill=PANEL)
        d.text(((x + KPI_W - 30) * S, (y + 30) * S), glyph, font=fonts("icons", 24), fill="#CFCFCF", anchor="mm")

    if path.exists():
        path.unlink()  # có thể thuộc root nếu Power BI đã lưu lại
    im.save(path, optimize=True)


def build_all(out_dir, font_dir, pages):
    """pages: danh sách dict có 'bg' (tên file) và 'kpi_icons'."""
    fonts = Fonts(font_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(pages):
        draw_page(out_dir / page["bg"], fonts, i, page["kpi_icons"])
