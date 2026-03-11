from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image
from PIL import ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "assets" / "champions"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "assets" / "tactics-cutouts"
OUTPUT_SIZE = (192, 256)

# Slight focal-point corrections for portraits that are not centered.
FOCUS_BY_FILENAME: dict[str, tuple[float, float]] = {
    "Ahri.png": (0.46, 0.45),
    "Akali.png": (0.52, 0.45),
    "Ashe.png": (0.48, 0.45),
    "Braum.png": (0.45, 0.42),
    "Caitlyn.png": (0.48, 0.44),
    "Ezreal.png": (0.52, 0.44),
    "Jinx.png": (0.58, 0.44),
    "Leona.png": (0.48, 0.42),
    "Orianna.png": (0.52, 0.44),
    "Riven.png": (0.43, 0.45),
    "Sett.png": (0.5, 0.4),
    "Yasuo.png": (0.52, 0.42),
    "Zed.png": (0.5, 0.42),
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def cover_crop(image: Image.Image, size: tuple[int, int], focus: tuple[float, float]) -> Image.Image:
    width, height = image.size
    target_width, target_height = size
    scale = max(target_width / width, target_height / height)
    resized = image.resize((max(1, round(width * scale)), max(1, round(height * scale))), Image.Resampling.LANCZOS)

    focus_x, focus_y = focus
    center_x = resized.width * focus_x
    center_y = resized.height * focus_y
    left = round(clamp(center_x - target_width / 2, 0, resized.width - target_width))
    top = round(clamp(center_y - target_height / 2, 0, resized.height - target_height))
    return resized.crop((left, top, left + target_width, top + target_height))


def shaped_mask(size: tuple[int, int]) -> Image.Image:
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=28, fill=255)

    taper = Image.new("L", size, 0)
    taper_draw = ImageDraw.Draw(taper)
    taper_draw.polygon(
        [
            (0, int(height * 0.76)),
            (int(width * 0.18), int(height * 0.64)),
            (int(width * 0.5), int(height * 0.74)),
            (int(width * 0.82), int(height * 0.64)),
            (width, int(height * 0.76)),
            (width, height),
            (0, height),
        ],
        fill=255,
    )
    mask.paste(0, mask=taper)

    for y in range(int(height * 0.58), height):
        alpha = int(255 * clamp((height - y) / max(1, height - int(height * 0.58)), 0.0, 1.0))
        draw.line((0, y, width, y), fill=alpha)
    return mask


def compose_cutout(image: Image.Image, size: tuple[int, int], focus: tuple[float, float]) -> Image.Image:
    base = cover_crop(image.convert("RGBA"), size, focus)
    cutout = Image.new("RGBA", size, (0, 0, 0, 0))
    cutout.alpha_composite(base)

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse((-18, 0, size[0] + 18, int(size[1] * 0.76)), fill=(255, 255, 255, 26))
    overlay_draw.rectangle((0, int(size[1] * 0.56), size[0], size[1]), fill=(7, 12, 20, 58))
    cutout.alpha_composite(overlay)

    mask = shaped_mask(size)
    cutout.putalpha(mask)

    edge = Image.new("RGBA", size, (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(edge)
    edge_draw.rounded_rectangle((1, 1, size[0] - 2, size[1] - 2), radius=28, outline=(255, 255, 255, 72), width=2)
    cutout.alpha_composite(edge)
    return cutout


def generate_cutouts(output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = 0
    for source_path in sorted(INPUT_DIR.glob("*.png")):
        focus = FOCUS_BY_FILENAME.get(source_path.name, (0.5, 0.44))
        image = Image.open(source_path)
        cutout = compose_cutout(image, OUTPUT_SIZE, focus)
        cutout.save(output_dir / source_path.name)
        generated += 1
    return generated


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate tactics cutout PNGs from portrait art.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write generated cutouts into.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    generated = generate_cutouts(args.output_dir)
    print(f"generated {generated} cutouts into {args.output_dir}")


if __name__ == "__main__":
    main()
