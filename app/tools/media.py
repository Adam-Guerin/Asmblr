from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable


def generate_diffusion_image(
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


def generate_video_from_image(
    image_path: Path,
    output_path: Path,
    model_id: str,
    num_frames: int,
    fps: int,
    device: str,
) -> None:
    try:
        from diffusers import StableVideoDiffusionPipeline
        import torch
        from PIL import Image
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("diffusers/torch/PIL not available") from exc

    torch_dtype = torch.float16 if device.startswith("cuda") else torch.float32
    pipe = StableVideoDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch_dtype)
    pipe.to(device)
    image = Image.open(image_path).convert("RGB")
    frames = pipe(image, num_frames=num_frames).frames[0]

    try:
        import imageio
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("imageio not available") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(output_path, fps=fps) as writer:
        for frame in frames:
            writer.append_data(frame)


def build_social_prompt(title: str, subtitle: str, keywords: Iterable[str]) -> str:
    keys = ", ".join([k for k in keywords if k]) or "clean, minimal, product UI"
    return f"Minimal product promo poster, bold typography, {keys}. Title: {title}. Subtitle: {subtitle}."
