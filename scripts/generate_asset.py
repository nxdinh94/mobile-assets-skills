#!/usr/bin/env python3
"""
Mobile Asset Generator - Generate graphics/icons via Nano Banana models.

Tries Nano Banana 2 (flash) first, falls back to Nano Banana Pro on failure.

Usage:
    python generate_asset.py "<concept>" --type icon --output icon.png
    python generate_asset.py "<concept>" --type splash --output splash.png -ar 9:16
    python generate_asset.py "<concept>" --type feature --output feature.png -ar 16:9
    python generate_asset.py "<concept>" --type illustration --output illust.png
"""

import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from remove_bg import remove_background

# Environment resolution
CLAUDE_ROOT = Path.home() / '.claude'
sys.path.insert(0, str(CLAUDE_ROOT / 'scripts'))
PROJECT_CLAUDE = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_CLAUDE / 'scripts'))
try:
    from resolve_env import resolve_env
    CENTRALIZED_RESOLVER = True
except ImportError:
    CENTRALIZED_RESOLVER = False
    try:
        from dotenv import load_dotenv
        load_dotenv(CLAUDE_ROOT / '.env')
        load_dotenv(CLAUDE_ROOT / 'skills' / '.env')
    except ImportError:
        pass

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


MODELS = {
    "flash": "gemini-2.5-flash-image",
    "pro": "gemini-3-pro-image-preview",
}

ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3",
    "4:5", "5:4", "9:16", "16:9", "21:9",
]

ASSET_PROMPTS = {
    "icon": (
        "A clean, modern mobile app icon for {concept}. "
        "Simple, bold design with a single recognizable symbol. "
        "Flat design with subtle gradients. No text, no labels, no watermarks. "
        "Centered composition, rounded square shape compatible. "
        "Professional quality, vibrant colors on a clean background. "
        "NEVER add any text or watermarks. DO NOT include labels."
    ),
    "splash": (
        "A beautiful mobile app splash screen for {concept}. "
        "Clean, centered composition with ample whitespace. "
        "Professional branding quality with subtle background elements. "
        "Elegant and minimal, suitable for app loading screen. "
        "NEVER add watermarks. DO NOT include unwanted text."
    ),
    "feature": (
        "A professional feature graphic banner for {concept}. "
        "Marketing quality, eye-catching design for app store listing. "
        "Bold typography-ready layout with strong visual hierarchy. "
        "Clean, modern design suitable for Google Play or App Store. "
        "NEVER add watermarks. DO NOT include unwanted labels."
    ),
    "illustration": (
        "A polished illustration for a mobile app about {concept}. "
        "Modern flat illustration style with clean lines. "
        "Suitable for onboarding screens or empty states. "
        "Consistent color palette, professional quality. "
        "NEVER add watermarks. DO NOT include labels."
    ),
    "in-app-icon": (
        "A simple, clean icon representing {concept}. "
        "Minimal line-art or flat design, single color works well. "
        "No background, transparent-ready. Bold, recognizable at small sizes. "
        "NEVER add text, watermarks, or labels."
    ),
}

DEFAULT_ASPECT = {
    "icon": "1:1",
    "splash": "9:16",
    "feature": "16:9",
    "illustration": "1:1",
    "in-app-icon": "1:1",
}


def get_api_key():
    if CENTRALIZED_RESOLVER:
        return resolve_env('GEMINI_API_KEY', skill='ai-multimodal')
    return os.getenv('GEMINI_API_KEY')


def generate_with_model(client, model_id, prompt, aspect_ratio, size):
    """Generate image with a specific model. Returns (bytes, model_id) or raises."""
    config_args = {'aspect_ratio': aspect_ratio}
    if 'pro' in model_id.lower() and size:
        config_args['image_size'] = size

    config = types.GenerateContentConfig(
        response_modalities=['IMAGE'],
        image_config=types.ImageConfig(**config_args),
    )

    response = client.models.generate_content(
        model=model_id,
        contents=[prompt],
        config=config,
    )

    if hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data, model_id

    raise RuntimeError("No image data in response")


def generate_asset(concept, asset_type, output_path, aspect_ratio=None,
                   size="2K", custom_prompt=None, verbose=False, dry_run=False,
                   remove_bg=True, bg_method="auto", bg_fuzz=10):
    """Generate a mobile asset image with Nano Banana 2 -> Pro fallback.
    Background removal is enabled by default for PNG output."""
    # Build prompt first (needed for dry-run)
    if custom_prompt:
        prompt = custom_prompt
    else:
        template = ASSET_PROMPTS.get(asset_type, ASSET_PROMPTS["illustration"])
        prompt = template.format(concept=concept)

    ar = aspect_ratio or DEFAULT_ASPECT.get(asset_type, "1:1")

    if verbose:
        print(f"[Asset Type] {asset_type}")
        print(f"[Aspect Ratio] {ar}")
        print(f"[Prompt] {prompt[:120]}...")

    if dry_run:
        print(f"[Dry run] Would generate to: {output_path}")
        print(f"[Prompt]\n{prompt}")
        return {"status": "dry_run", "prompt": prompt}

    if not HAS_GENAI:
        return {"status": "error", "error": "google-genai not installed. Run: pip install google-genai"}

    api_key = get_api_key()
    if not api_key:
        return {"status": "error", "error": "GEMINI_API_KEY not found"}

    client = genai.Client(api_key=api_key)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Try Nano Banana 2 (flash) first, then Pro
    models_to_try = [("flash", MODELS["flash"]), ("pro", MODELS["pro"])]
    last_error = None

    for label, model_id in models_to_try:
        try:
            if verbose:
                print(f"[Trying] {label} ({model_id})...")

            data, used_model = generate_with_model(client, model_id, prompt, ar, size)

            with open(out, 'wb') as f:
                f.write(data)

            if verbose:
                print(f"[Success] Generated with {label}: {out}")

            # Remove background if requested
            if remove_bg:
                if verbose:
                    print(f"[Removing background]...")
                bg_result = remove_background(
                    src=str(out), dst=str(out),
                    method=bg_method, fuzz=bg_fuzz, verbose=verbose,
                )
                if bg_result["status"] != "success":
                    if verbose:
                        print(f"[Warning] Background removal failed: {bg_result['error']}")
                elif verbose:
                    print(f"[Background removed] method: {bg_result['method']}")

            return {
                "status": "success",
                "output": str(out),
                "model": used_model,
                "asset_type": asset_type,
                "bg_removed": remove_bg,
            }
        except Exception as e:
            last_error = str(e)
            if verbose:
                print(f"[Failed] {label}: {last_error}")

    return {"status": "error", "error": f"All models failed. Last: {last_error}"}


def main():
    parser = argparse.ArgumentParser(
        description="Mobile Asset Generator - Nano Banana image generation",
    )
    parser.add_argument("concept", help="Concept/subject to generate")
    parser.add_argument("--type", "-t", choices=list(ASSET_PROMPTS.keys()),
                        default="icon", help="Asset type (default: icon)")
    parser.add_argument("--output", "-o", required=True, help="Output image path")
    parser.add_argument("--aspect-ratio", "-ar", choices=ASPECT_RATIOS, default=None,
                        help="Override aspect ratio")
    parser.add_argument("--size", choices=["1K", "2K", "4K"], default="2K")
    parser.add_argument("--prompt", "-p", default=None, help="Custom prompt override")
    parser.add_argument("--remove-bg", action="store_true", default=True,
                        help="Remove background for transparent PNG (default: on)")
    parser.add_argument("--no-remove-bg", dest="remove_bg", action="store_false",
                        help="Keep original background")
    parser.add_argument("--bg-method",
                        choices=["auto", "birefnet", "u2net", "isnet", "magick"],
                        default="auto", help="Background removal method (default: auto = birefnet)")
    parser.add_argument("--bg-fuzz", type=int, default=10,
                        help="Fuzz %% for magick bg removal (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Show prompt without generating")

    args = parser.parse_args()

    result = generate_asset(
        concept=args.concept,
        asset_type=args.type,
        output_path=args.output,
        aspect_ratio=args.aspect_ratio,
        size=args.size,
        custom_prompt=args.prompt,
        verbose=args.verbose,
        dry_run=args.dry_run,
        remove_bg=args.remove_bg,
        bg_method=args.bg_method,
        bg_fuzz=args.bg_fuzz,
    )

    if result["status"] == "success":
        print(f"Generated: {result['output']} (model: {result['model']})")
    elif result["status"] == "error":
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
