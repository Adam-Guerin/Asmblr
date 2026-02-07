from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable


def generate_logo_png(
    output_path: Path,
    prompt: str,
    model_id: str,
    size: int,
    steps: int,
    guidance: float,
    seed: int | None,
    device: str,
) -> None:
    try:
        from diffusers import StableDiffusionPipeline
        import torch
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("diffusers/torch not available") from exc

    torch_dtype = torch.float16 if device.startswith("cuda") else torch.float32
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        safety_checker=None,
    )
    pipe.to(device)
    generator = torch.Generator(device=device).manual_seed(seed) if seed is not None else None
    image = pipe(
        prompt,
        num_inference_steps=steps,
        guidance_scale=guidance,
        width=size,
        height=size,
        generator=generator,
    ).images[0]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def quantize_png_three_colors(input_path: Path, output_path: Path) -> None:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Pillow not available") from exc

    img = Image.open(input_path).convert("RGB")
    method = getattr(Image, "FASTOCTREE", Image.MEDIANCUT)
    quantized = img.quantize(colors=3, method=method)
    quantized = quantized.convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    quantized.save(output_path)


def png_to_svg_three_colors(input_path: Path, output_path: Path) -> None:
    try:
        import vtracer
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("vtracer not available") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    vtracer.convert_image_to_svg(
        str(input_path),
        str(output_path),
        colormode="color",
        colors=3,
        mode="polygon",
        hierarchical="stacked",
        filter_speckle=4,
    )


def first_three_colors(colors: Iterable[str]) -> list[str]:
    selected: list[str] = []
    for item in colors:
        if not item:
            continue
        selected.append(item)
        if len(selected) >= 3:
            break
    return selected
