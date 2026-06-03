"""4コマ漫画画像を生成する (1080x1080px / Instagram正方形)"""
import sys
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))
from fetch_irasutoya import fetch as _fetch

# ── キャンバス設定 ──────────────────────────────────────────
CANVAS_W, CANVAS_H = 1080, 1080
TITLE_H = 100
PAD = 10

# ── カラーパレット ──────────────────────────────────────────
BG_COLOR       = "#FFF8F0"
PANEL_BG       = "#FFFFFF"
PANEL_BORDER   = "#E0E0E0"
TEXT_BOX_BG    = "#F0F7FF"
TEXT_COLOR     = "#333333"
PLACEHOLDER_BG = "#F0F0F0"
PLACEHOLDER_FG = "#AAAAAA"
CATEGORY_COLOR = {"賃貸": "#2D6A4F", "売買": "#C1440E"}

ROOT       = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "output"


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap(text: str, font, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """日本語対応の文字単位折り返し"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        test = cur + ch
        if draw.textbbox((0, 0), test, font=font)[2] > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def _load_image(keyword: str, max_w: int, max_h: int) -> Image.Image:
    path = _fetch(keyword)
    if path:
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            return img
        except Exception:
            pass
    # プレースホルダー
    ph = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ph)
    d.rounded_rectangle([0, 0, max_w - 1, max_h - 1], radius=10,
                         fill=PLACEHOLDER_BG, outline="#CCCCCC", width=1)
    font = _get_font(16)
    label = keyword[:10]
    d.text((max_w // 2, max_h // 2), label, font=font,
           fill=PLACEHOLDER_FG, anchor="mm", align="center")
    return ph


def _draw_panel(canvas: Image.Image, draw: ImageDraw.ImageDraw,
                x: int, y: int, w: int, h: int, panel: dict) -> None:
    # パネル背景
    draw.rounded_rectangle([x, y, x + w, y + h], radius=12,
                            fill=PANEL_BG, outline=PANEL_BORDER, width=2)

    # キャラクター画像エリア (上60%)
    img_h = int(h * 0.60)
    char = _load_image(panel.get("image", "happy_person"), w - 20, img_h - 10)
    paste_x = x + (w - char.width) // 2
    paste_y = y + 5
    if char.mode == "RGBA":
        canvas.paste(char, (paste_x, paste_y), char)
    else:
        canvas.paste(char, (paste_x, paste_y))

    # テキストエリア (下40%)
    tx, ty = x + 8, y + img_h + 5
    tw, th = w - 16, h - img_h - 10
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=8, fill=TEXT_BOX_BG)

    font = _get_font(22)
    lines = _wrap(panel.get("text", ""), font, tw - 16, draw)
    lh = 27
    total = len(lines) * lh
    start_y = ty + max(6, (th - total) // 2)
    for i, line in enumerate(lines):
        draw.text((x + w // 2, start_y + i * lh), line,
                  font=font, fill=TEXT_COLOR, anchor="mm")


def compose(story: dict, episode_num: int, output_path: str | None = None) -> str:
    """
    story: stories.json の1要素
    episode_num: 投稿通し番号
    output_path: 保存先（省略時は output/episode_NNN.png）
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    if output_path is None:
        output_path = str(OUTPUT_DIR / f"episode_{episode_num:03d}.png")

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw   = ImageDraw.Draw(canvas)

    # ── タイトルバー ──────────────────────────────────────
    cat   = story.get("category", "賃貸")
    color = CATEGORY_COLOR.get(cat, "#2D6A4F")
    draw.rectangle([0, 0, CANVAS_W, TITLE_H], fill=color)

    # カテゴリバッジ
    badge_font = _get_font(20)
    draw.rounded_rectangle([12, 14, 78, 44], radius=8, fill="white")
    draw.text((45, 29), cat, font=badge_font, fill=color, anchor="mm")

    # タイトル & サブタイトル
    draw.text((CANVAS_W // 2, 36),
              "不動産あるある", font=_get_font(34), fill="white", anchor="mm")
    draw.text((CANVAS_W // 2, 74),
              f"#{episode_num:02d}「{story['title']}」",
              font=_get_font(22), fill="#D8EED8", anchor="mm")

    # ── パネル配置 ────────────────────────────────────────
    panels = story["panels"][:4]
    n      = len(panels)
    cols   = 1 if n <= 2 else 2
    rows   = (n + cols - 1) // cols

    area_x = PAD
    area_y = TITLE_H + PAD
    area_w = CANVAS_W - PAD * 2
    area_h = CANVAS_H - TITLE_H - PAD * 2

    pw = (area_w - PAD * (cols - 1)) // cols
    ph = (area_h - PAD * (rows - 1)) // rows

    for i, panel in enumerate(panels):
        col = i % cols
        row = i // cols
        px  = area_x + col * (pw + PAD)
        py  = area_y + row * (ph + PAD)
        _draw_panel(canvas, draw, px, py, pw, ph, panel)

    canvas.save(output_path, "PNG")
    return output_path


# ── テスト実行 ────────────────────────────────────────────
if __name__ == "__main__":
    import json, sys
    stories = json.loads((ROOT / "content" / "stories.json").read_text(encoding="utf-8"))
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    story = stories[idx % len(stories)]
    out = compose(story, idx + 1)
    print(f"生成完了: {out}")
