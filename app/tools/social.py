from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _parse_hex_color(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        return (17, 17, 17)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def pick_palette(colors: Iterable[str]) -> list[tuple[int, int, int]]:
    selected: list[tuple[int, int, int]] = []
    for item in colors:
        if not item:
            continue
        selected.append(_parse_hex_color(item))
        if len(selected) >= 3:
            break
    if not selected:
        selected = [(17, 17, 17), (34, 197, 94), (249, 250, 251)]
    while len(selected) < 3:
        selected.append(selected[-1])
    return selected


def generate_social_image(
    output_path: Path,
    title: str,
    subtitle: str,
    palette_hex: Iterable[str],
    size: tuple[int, int],
) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Pillow not available") from exc

    width, height = size
    bg, accent, text_color = pick_palette(palette_hex)
    image = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(image)

    pad = int(width * 0.07)
    draw.rectangle([pad, pad, width - pad, height - pad], outline=accent, width=6)

    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()

    title_text = title.strip() or "New Product"
    subtitle_text = subtitle.strip() or "Discover the MVP launch pack."

    draw.text((pad + 20, pad + 20), title_text, fill=text_color, font=title_font)
    draw.text((pad + 20, pad + 70), subtitle_text, fill=text_color, font=subtitle_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
