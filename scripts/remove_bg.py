#!/usr/bin/env python3
"""
Background Remover - Remove background from images for transparent PNGs.

Uses rembg (Python, BiRefNet model) for best quality. Falls back to ImageMagick.

Usage:
    python remove_bg.py input.png -o output.png
    python remove_bg.py input.png -o output.png --method birefnet
    python remove_bg.py input.png -o output.png --method u2net
    python remove_bg.py input.png -o output.png --method magick --fuzz 15
    python remove_bg.py input.png  # overwrites input

Methods:
    birefnet      - BiRefNet model (best quality, default)
    u2net         - U2Net model (faster, good quality)
    isnet         - ISNet general-use model
    magick        - ImageMagick flood-fill (color-based, solid backgrounds only)

Install: pip install "rembg[cpu]"
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def has_tool(name):
    return shutil.which(name) is not None


def remove_bg_rembg(src, dst, model="birefnet-general", verbose=False):
    """Remove background using rembg Python library (AI-powered)."""
    try:
        from rembg import remove, new_session
    except ImportError:
        return {"status": "error", "error": 'rembg not installed. Run: pip install "rembg[cpu]"'}

    if verbose:
        print(f"[rembg] model={model}, {src} -> {dst}")

    try:
        session = new_session(model_name=model)

        with open(src, 'rb') as f:
            input_data = f.read()

        output_data = remove(input_data, session=session)

        with open(dst, 'wb') as f:
            f.write(output_data)

        return {"status": "success", "output": str(dst), "method": f"rembg-{model}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def remove_bg_magick(src, dst, fuzz=10, verbose=False):
    """Remove background using ImageMagick flood-fill (for solid backgrounds)."""
    if not has_tool("magick"):
        return {"status": "error", "error": "ImageMagick not found. Install: brew install imagemagick"}

    cmd = [
        "magick", str(src),
        "-fuzz", f"{fuzz}%",
        "-fill", "none",
        "-draw", "color 0,0 floodfill",
        "-draw", "color 0,%[fx:h-1] floodfill",
        "-draw", "color %[fx:w-1],0 floodfill",
        "-draw", "color %[fx:w-1],%[fx:h-1] floodfill",
        str(dst),
    ]

    if verbose:
        print(f"[magick] fuzz={fuzz}%, {src} -> {dst}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"status": "error", "error": f"magick failed: {result.stderr.strip()}"}

        return {"status": "success", "output": str(dst), "method": f"magick-fuzz{fuzz}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Map user-facing method names to rembg model names
REMBG_MODELS = {
    "birefnet": "birefnet-general",
    "u2net": "u2net",
    "isnet": "isnet-general-use",
}


def remove_background(src, dst=None, method="auto", fuzz=10, verbose=False):
    """Remove background from image.

    Args:
        src: Source image path
        dst: Output path (default: overwrite source)
        method: 'auto', 'birefnet', 'u2net', 'isnet', 'magick'
        fuzz: Fuzz percentage for ImageMagick method (default: 10)
        verbose: Print progress

    Returns:
        dict with status, output, method
    """
    src = Path(src)
    if not src.exists():
        return {"status": "error", "error": f"File not found: {src}"}

    if dst is None:
        dst = src
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.suffix.lower() not in ('.png', '.webp'):
        dst = dst.with_suffix('.png')
        if verbose:
            print(f"[Note] Output changed to PNG for transparency: {dst}")

    if method == "auto":
        # Try rembg with birefnet first (best quality), fall back to magick
        result = remove_bg_rembg(src, dst, model="birefnet-general", verbose=verbose)
        if result["status"] == "success":
            return result
        if verbose:
            print(f"[auto] rembg failed, trying magick: {result['error']}")

        if has_tool("magick"):
            return remove_bg_magick(src, dst, fuzz=fuzz, verbose=verbose)

        return {"status": "error", "error": 'No bg removal tool found. Install: pip install "rembg[cpu]"'}

    elif method in REMBG_MODELS:
        return remove_bg_rembg(src, dst, model=REMBG_MODELS[method], verbose=verbose)

    elif method == "magick":
        return remove_bg_magick(src, dst, fuzz=fuzz, verbose=verbose)

    return {"status": "error", "error": f"Unknown method: {method}"}


def main():
    parser = argparse.ArgumentParser(
        description="Remove background from images for transparent PNGs",
    )
    parser.add_argument("input", help="Source image path")
    parser.add_argument("--output", "-o", default=None,
                        help="Output path (default: overwrite input)")
    parser.add_argument("--method", "-m",
                        choices=["auto", "birefnet", "u2net", "isnet", "magick"],
                        default="auto", help="Removal method (default: auto = birefnet)")
    parser.add_argument("--fuzz", type=int, default=10,
                        help="Fuzz %% for magick method (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    result = remove_background(
        src=args.input,
        dst=args.output,
        method=args.method,
        fuzz=args.fuzz,
        verbose=args.verbose,
    )

    if result["status"] == "success":
        print(f"Background removed: {result['output']} (method: {result['method']})")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
