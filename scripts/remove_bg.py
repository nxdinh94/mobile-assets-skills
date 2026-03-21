#!/usr/bin/env python3
"""
Background Remover - Remove background from images for transparent PNGs.

Uses rmbg (AI-powered, best quality) with ImageMagick fallback.

Usage:
    python remove_bg.py input.png -o output.png
    python remove_bg.py input.png -o output.png --method rmbg-briaai
    python remove_bg.py input.png -o output.png --method magick --fuzz 15
    python remove_bg.py input.png  # overwrites input

Methods:
    rmbg          - Default rmbg model (modnet), good general-purpose
    rmbg-briaai   - High quality AI model (slower, best results)
    rmbg-u2netp   - Fast AI model (quick, decent results)
    magick        - ImageMagick flood-fill removal (color-based, for solid backgrounds)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def has_tool(name):
    return shutil.which(name) is not None


def remove_bg_rmbg(src, dst, model="modnet", verbose=False):
    """Remove background using rmbg CLI (AI-powered)."""
    if not has_tool("rmbg"):
        return {"status": "error", "error": "rmbg not found. Install: npm install -g rmbg-cli"}

    cmd = ["rmbg", str(src), "-o", str(dst)]

    if model == "briaai":
        cmd.extend(["-m", "briaai"])
    elif model == "u2netp":
        cmd.extend(["-m", "u2netp"])

    if verbose:
        print(f"[rmbg] model={model}, {src} -> {dst}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return {"status": "error", "error": f"rmbg failed: {result.stderr.strip()}"}

        return {"status": "success", "output": str(dst), "method": f"rmbg-{model}"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "rmbg timed out (120s)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def remove_bg_magick(src, dst, fuzz=10, verbose=False):
    """Remove background using ImageMagick flood-fill (for solid backgrounds)."""
    if not has_tool("magick"):
        return {"status": "error", "error": "ImageMagick not found. Install: brew install imagemagick"}

    # Strategy: flood-fill from corners to remove solid background color
    # Works well for icons generated with solid/near-solid backgrounds
    cmd = [
        "magick", str(src),
        "-fuzz", f"{fuzz}%",
        "-fill", "none",
        "-draw", "color 0,0 floodfill",          # top-left corner
        "-draw", "color 0,%[fx:h-1] floodfill",   # bottom-left corner
        "-draw", "color %[fx:w-1],0 floodfill",   # top-right corner
        "-draw", "color %[fx:w-1],%[fx:h-1] floodfill",  # bottom-right corner
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


def remove_background(src, dst=None, method="auto", fuzz=10, verbose=False):
    """Remove background from image.

    Args:
        src: Source image path
        dst: Output path (default: overwrite source)
        method: 'auto', 'rmbg', 'rmbg-briaai', 'rmbg-u2netp', 'magick'
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

    # Ensure output is PNG (transparency requires it)
    if dst.suffix.lower() not in ('.png', '.webp'):
        dst = dst.with_suffix('.png')
        if verbose:
            print(f"[Note] Output changed to PNG for transparency: {dst}")

    if method == "auto":
        # Try rmbg-briaai first (best quality), fall back to magick
        if has_tool("rmbg"):
            result = remove_bg_rmbg(src, dst, model="briaai", verbose=verbose)
            if result["status"] == "success":
                return result
            if verbose:
                print(f"[auto] rmbg-briaai failed, trying magick: {result['error']}")

        if has_tool("magick"):
            return remove_bg_magick(src, dst, fuzz=fuzz, verbose=verbose)

        return {"status": "error", "error": "No bg removal tool found. Install rmbg or imagemagick"}

    elif method.startswith("rmbg"):
        model = "modnet"
        if method == "rmbg-briaai":
            model = "briaai"
        elif method == "rmbg-u2netp":
            model = "u2netp"
        return remove_bg_rmbg(src, dst, model=model, verbose=verbose)

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
                        choices=["auto", "rmbg", "rmbg-briaai", "rmbg-u2netp", "magick"],
                        default="auto", help="Removal method (default: auto)")
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
