import asyncio
import io
import logging
import os
import random
import time
import uuid
from typing import Optional

import requests
from PIL import Image

logger = logging.getLogger(__name__)

THUMBNAILS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend", "thumbnails"
)

# Models that use local diffusers inference instead of HF Inference API
LOCAL_DIFFUSERS_MODELS = {"flux1-dev"}

# Check if Cosmos3OmniPipeline is available (requires git version of diffusers)
_COSMOS3_AVAILABLE = False
try:
    from diffusers import Cosmos3OmniPipeline
    from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
    _COSMOS3_AVAILABLE = True
    LOCAL_DIFFUSERS_MODELS.add("cosmos3-t2i")
except ImportError:
    logger.info("Cosmos3OmniPipeline not available in installed diffusers; cosmos3-t2i will use HF Inference API")

HF_MODELS = {
    "flux1-dev":       "black-forest-labs/FLUX.1-dev",
    "sd35-large":      "stabilityai/stable-diffusion-3.5-large",
    "qwen-image":      "alibaba-qwen/Qwen-Image",
    "qwen-image-edit": "alibaba-qwen/Qwen-Image-Edit",
    "cosmos3-t2i":     "nvidia/Cosmos3-Nano",
}

def _get_hf_token():
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN") or None

# Lazy-loaded diffusers pipeline cache
_model_pipelines = {}

def _get_pipeline(model_key: str):
    if model_key in _model_pipelines:
        return _model_pipelines[model_key]

    import torch
    token = _get_hf_token()

    if model_key == "flux1-dev":
        from diffusers import FluxPipeline
        pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            torch_dtype=torch.bfloat16,
            token=token,
        )
        pipe.enable_model_cpu_offload()
    elif model_key == "cosmos3-t2i":
        pipe = Cosmos3OmniPipeline.from_pretrained(
            "nvidia/Cosmos3-Nano",
            torch_dtype=torch.bfloat16,
            token=token,
        )
        pipe.scheduler = UniPCMultistepScheduler.from_config(
            pipe.scheduler.config, flow_shift=3.0
        )
        pipe.enable_model_cpu_offload()
    else:
        raise ValueError(f"No local diffusers pipeline for model: {model_key}")

    _model_pipelines[model_key] = pipe
    return pipe


def _diffusers_infer(
    model_key: str,
    prompt: str,
    negative_prompt: str = "",
    width: int = 1280,
    height: int = 720,
    guidance_scale: float = 7.5,
    num_inference_steps: int = 35,
) -> bytes:
    import torch
    pipe = _get_pipeline(model_key)

    if model_key == "flux1-dev":
        image = pipe(
            prompt,
            height=height,
            width=width,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            max_sequence_length=512,
            generator=torch.Generator("cpu").manual_seed(random.randint(0, 2**32 - 1)),
        ).images[0]
    elif model_key == "cosmos3-t2i":
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt or "",
            num_frames=1,
            height=height,
            width=width,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
        )
        image = result.video[0]

    buf = io.BytesIO()
    if image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(buf, format="PNG")
    return buf.getvalue()


def _hf_infer(
    model_id: str,
    prompt: str,
    negative_prompt: str = "",
    width: int = 1280,
    height: int = 720,
    guidance_scale: float = 7.5,
    num_inference_steps: int = 35,
) -> bytes:
    _token = _get_hf_token()
    headers = {"Authorization": f"Bearer {_token}"} if _token else {}
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        },
    }
    logger.debug("HF inference payload keys: %s", list(payload["parameters"].keys()))

    max_retries = int(os.environ.get("HF_MAX_RETRIES", "3"))
    backoff_base = float(os.environ.get("HF_BACKOFF_BASE", "1.0"))
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                f"https://api-inference.huggingface.co/models/{model_id}",
                headers=headers,
                json=payload,
                timeout=120,
            )
            ct = resp.headers.get("content-type", "")
            if resp.status_code != 200:
                msg = resp.text[:1000] if resp.text else f"status {resp.status_code}"
                raise RuntimeError(f"HF Inference API error ({resp.status_code}): {msg}")
            if "application/json" in ct:
                # HF may return JSON with error details instead of image bytes
                raise RuntimeError(f"HF Inference API returned json response: {resp.text[:1000]}")
            return resp.content
        except Exception as e:
            last_exc = e
            logger.warning("HF inference attempt %d/%d failed for %s: %s", attempt, max_retries, model_id, e)
            if attempt < max_retries:
                sleep_for = backoff_base * (2 ** (attempt - 1))
                # add small jitter
                sleep_for = sleep_for + (0.1 * attempt)
                time.sleep(sleep_for)
            else:
                # final failure
                err_msg = str(last_exc)
                raise RuntimeError(
                    f"HF Inference failed after {max_retries} attempts: {err_msg}. "
                    "This is likely a network or DNS error — check connectivity and HF_TOKEN configuration."
                )


async def generate_image(
    model_key: str,
    prompt: str,
    negative_prompt: str = "",
    width: int = 1280,
    height: int = 720,
    **kwargs,
) -> Optional[dict]:
    model_id = HF_MODELS.get(model_key)
    if not model_id:
        raise ValueError(f"Unknown model: {model_key}")

    os.makedirs(THUMBNAILS_DIR, exist_ok=True)
    gen_id = uuid.uuid4().hex[:12]
    output_path = os.path.join(THUMBNAILS_DIR, f"{gen_id}_{model_key}.png")
    thumb_path = os.path.join(THUMBNAILS_DIR, f"{gen_id}_{model_key}_thumb.png")

    def _run():
        t0 = time.time()
        # allow callers to override sampling params via kwargs
        guidance_scale = float(kwargs.get("guidance_scale", kwargs.get("guidance", 7.5)))
        num_inference_steps = int(kwargs.get("num_inference_steps", kwargs.get("steps", 35)))
        logger.info("Generating image: model=%s prompt_len=%d guidance=%s steps=%s", model_key, len(prompt or ""), guidance_scale, num_inference_steps)

        if model_key in LOCAL_DIFFUSERS_MODELS:
            image_data = _diffusers_infer(
                model_key,
                prompt,
                negative_prompt,
                width,
                height,
                guidance_scale,
                num_inference_steps,
            )
        else:
            image_data = _hf_infer(
                model_id,
                prompt,
                negative_prompt,
                width,
                height,
                guidance_scale,
                num_inference_steps,
            )

        img = Image.open(io.BytesIO(image_data))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(output_path, "PNG")
        thumb = img.copy()
        thumb.thumbnail((640, 360))
        thumb.save(thumb_path, "PNG")
        gen_time_ms = int((time.time() - t0) * 1000)
        return {
            "image_url": f"/api/thumbnails/{os.path.basename(output_path)}",
            "thumbnail_url": f"/api/thumbnails/{os.path.basename(thumb_path)}",
            "generation_time_ms": gen_time_ms,
        }

    return await asyncio.to_thread(_run)
