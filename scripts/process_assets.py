#!/usr/bin/env python3
"""
Mobile Asset Processor - Resize and deploy generated images to platform-specific directories.

Auto-detects project type (Android, iOS, Flutter, React Native) and outputs
assets to the correct directories at all required sizes.

Usage:
    python process_assets.py <source.png> --type icon --project-dir /path/to/project
    python process_assets.py <source.png> --type splash --platform android
    python process_assets.py <source.png> --type icon --platform all --output-dir ./out

Requires: ImageMagick (magick command)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from remove_bg import remove_background

# --- Platform asset specifications ---

ANDROID_ICON_SPECS = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

ANDROID_ADAPTIVE_SPECS = {
    "mipmap-mdpi": 108,
    "mipmap-hdpi": 162,
    "mipmap-xhdpi": 216,
    "mipmap-xxhdpi": 324,
    "mipmap-xxxhdpi": 432,
}

ANDROID_PLAY_STORE_SIZE = 512

IOS_ICON_SPECS = {
    "20@1x": 20, "20@2x": 40, "20@3x": 60,
    "29@1x": 29, "29@2x": 58, "29@3x": 87,
    "40@1x": 40, "40@2x": 80, "40@3x": 120,
    "60@2x": 120, "60@3x": 180,
    "76@1x": 76, "76@2x": 152,
    "83.5@2x": 167,
    "1024@1x": 1024,
}

FLUTTER_WEB_FAVICONS = {
    "Icon-192": 192,
    "Icon-512": 512,
    "Icon-maskable-192": 192,
    "Icon-maskable-512": 512,
    "favicon": 16,
}

RN_DENSITIES = {"": 1, "@2x": 2, "@3x": 3}
RN_BASE_ICON_SIZE = 1024

SPLASH_SPECS = {
    "android": {
        "drawable-mdpi": (320, 480),
        "drawable-hdpi": (480, 800),
        "drawable-xhdpi": (720, 1280),
        "drawable-xxhdpi": (1080, 1920),
        "drawable-xxxhdpi": (1440, 2560),
    },
    "ios": {
        "Default@2x~universal~anyany": (2732, 2732),
        "Default@2x~universal~comany": (1278, 2732),
        "Default@2x~universal~comcom": (1278, 1278),
        "Default@3x~universal~anyany": (2208, 2208),
        "Default@3x~universal~comany": (828, 1792),
    },
}


def check_imagemagick():
    """Verify ImageMagick is available."""
    try:
        subprocess.run(["magick", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def resize_image(src, dst, width, height=None, verbose=False):
    """Resize image using ImageMagick."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if height:
        geometry = f"{width}x{height}!"
    else:
        geometry = f"{width}x{width}!"

    cmd = ["magick", str(src), "-resize", geometry, "-strip", str(dst)]

    if verbose:
        print(f"  {dst.name} ({width}{'x'+str(height) if height else 'x'+str(width)})")

    subprocess.run(cmd, check=True, capture_output=True)
    return str(dst)


def detect_project_type(project_dir):
    """Auto-detect mobile project type from directory structure."""
    p = Path(project_dir)
    detected = []

    # Android
    if (p / "app" / "src" / "main" / "AndroidManifest.xml").exists():
        detected.append("android")
    elif (p / "android" / "app" / "src" / "main" / "AndroidManifest.xml").exists():
        detected.append("android")

    # iOS
    if any(p.glob("*.xcodeproj")) or any(p.glob("*.xcworkspace")):
        detected.append("ios")
    elif any((p / "ios").glob("*.xcodeproj")) or any((p / "ios").glob("*.xcworkspace")):
        detected.append("ios")

    # Flutter
    if (p / "pubspec.yaml").exists():
        detected.append("flutter")

    # React Native
    if (p / "app.json").exists() and (p / "package.json").exists():
        try:
            pkg = json.loads((p / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "react-native" in deps:
                detected.append("react-native")
        except (json.JSONDecodeError, OSError):
            pass

    return detected or ["unknown"]


def get_android_res_dir(project_dir):
    """Find Android res directory."""
    p = Path(project_dir)
    candidates = [
        p / "app" / "src" / "main" / "res",
        p / "android" / "app" / "src" / "main" / "res",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # default


def get_ios_assets_dir(project_dir):
    """Find iOS Assets.xcassets directory."""
    p = Path(project_dir)
    candidates = list(p.rglob("Assets.xcassets"))
    # Prefer ios/ subdirectory
    for c in candidates:
        if "ios" in str(c).lower():
            return c
    return candidates[0] if candidates else p / "ios" / "Runner" / "Assets.xcassets"


def process_android_icons(src, res_dir, icon_name="ic_launcher", verbose=False):
    """Generate Android mipmap icons at all densities."""
    outputs = []
    if verbose:
        print("[Android Icons]")

    for density, size in ANDROID_ICON_SPECS.items():
        dst = res_dir / density / f"{icon_name}.png"
        resize_image(src, dst, size, verbose=verbose)
        outputs.append(str(dst))

    # Play Store icon
    dst = res_dir / ".." / "ic_launcher-playstore.png"
    resize_image(src, dst.resolve(), ANDROID_PLAY_STORE_SIZE, verbose=verbose)
    outputs.append(str(dst.resolve()))

    return outputs


def process_android_adaptive(src, res_dir, layer="foreground", verbose=False):
    """Generate Android adaptive icon layers."""
    outputs = []
    name = f"ic_launcher_{layer}"
    if verbose:
        print(f"[Android Adaptive - {layer}]")

    for density, size in ANDROID_ADAPTIVE_SPECS.items():
        dst = res_dir / density / f"{name}.png"
        resize_image(src, dst, size, verbose=verbose)
        outputs.append(str(dst))

    return outputs


def process_ios_icons(src, assets_dir, verbose=False):
    """Generate iOS AppIcon.appiconset at all sizes."""
    outputs = []
    iconset = assets_dir / "AppIcon.appiconset"
    iconset.mkdir(parents=True, exist_ok=True)

    if verbose:
        print("[iOS Icons]")

    contents_images = []
    for spec_name, size in IOS_ICON_SPECS.items():
        filename = f"Icon-App-{spec_name}.png"
        dst = iconset / filename
        resize_image(src, dst, size, verbose=verbose)
        outputs.append(str(dst))

        # Parse scale from spec name
        if "@" in spec_name:
            parts = spec_name.split("@")
            base_size = parts[0]
            scale = parts[1]
        else:
            base_size = str(size)
            scale = "1x"

        contents_images.append({
            "size": f"{base_size}x{base_size}",
            "idiom": "universal",
            "filename": filename,
            "scale": scale,
        })

    # Write Contents.json
    contents = {
        "images": contents_images,
        "info": {"version": 1, "author": "mobile-assets-skills"},
    }
    contents_path = iconset / "Contents.json"
    contents_path.write_text(json.dumps(contents, indent=2))
    outputs.append(str(contents_path))

    return outputs


def process_flutter_icons(src, project_dir, verbose=False):
    """Generate Flutter app icons (Android + iOS + web)."""
    p = Path(project_dir)
    outputs = []

    # Android icons
    android_res = get_android_res_dir(project_dir)
    outputs.extend(process_android_icons(src, android_res, verbose=verbose))

    # iOS icons
    ios_assets = get_ios_assets_dir(project_dir)
    outputs.extend(process_ios_icons(src, ios_assets, verbose=verbose))

    # Web favicons
    web_dir = p / "web"
    if web_dir.exists():
        if verbose:
            print("[Flutter Web Icons]")
        for name, size in FLUTTER_WEB_FAVICONS.items():
            ext = ".ico" if name == "favicon" else ".png"
            dst = web_dir / "icons" / f"{name}{ext}" if name != "favicon" else web_dir / f"{name}.png"
            resize_image(src, dst, size, verbose=verbose)
            outputs.append(str(dst))

    return outputs


def process_rn_icons(src, project_dir, icon_name="AppIcon", verbose=False):
    """Generate React Native app icons (Android + iOS)."""
    outputs = []

    # Android
    android_res = get_android_res_dir(project_dir)
    outputs.extend(process_android_icons(src, android_res, verbose=verbose))

    # iOS
    ios_assets = get_ios_assets_dir(project_dir)
    outputs.extend(process_ios_icons(src, ios_assets, verbose=verbose))

    return outputs


def process_splash_screens(src, project_dir, platforms=None, verbose=False):
    """Generate splash screen images for specified platforms."""
    outputs = []
    platforms = platforms or ["android", "ios"]

    for platform in platforms:
        specs = SPLASH_SPECS.get(platform, {})
        if verbose:
            print(f"[{platform.title()} Splash Screens]")

        if platform == "android":
            res_dir = get_android_res_dir(project_dir)
            for density, (w, h) in specs.items():
                dst = res_dir / density / "launch_background.png"
                resize_image(src, dst, w, h, verbose=verbose)
                outputs.append(str(dst))

        elif platform == "ios":
            ios_assets = get_ios_assets_dir(project_dir)
            splash_dir = ios_assets / "LaunchImage.imageset"
            splash_dir.mkdir(parents=True, exist_ok=True)
            for name, (w, h) in specs.items():
                dst = splash_dir / f"{name}.png"
                resize_image(src, dst, w, h, verbose=verbose)
                outputs.append(str(dst))

    return outputs


def process_generic(src, output_dir, sizes, name_prefix="asset", verbose=False):
    """Generate generic sized assets to a custom output directory."""
    outputs = []
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"[Generic Assets -> {out}]")

    for size in sizes:
        if "x" in size:
            w, h = map(int, size.split("x"))
        else:
            w, h = int(size), int(size)
        dst = out / f"{name_prefix}_{w}x{h}.png"
        resize_image(src, dst, w, h, verbose=verbose)
        outputs.append(str(dst))

    return outputs


def main():
    parser = argparse.ArgumentParser(
        description="Process mobile assets to platform-specific sizes and directories",
    )
    parser.add_argument("source", help="Source image path")
    parser.add_argument("--type", "-t", choices=["icon", "splash", "feature", "generic"],
                        default="icon", help="Asset type to process")
    parser.add_argument("--project-dir", "-d", default=".",
                        help="Project root directory (default: current)")
    parser.add_argument("--platform", "-p",
                        choices=["android", "ios", "flutter", "react-native", "all", "auto"],
                        default="auto", help="Target platform (default: auto-detect)")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="Custom output directory (overrides auto-detection)")
    parser.add_argument("--icon-name", default="ic_launcher",
                        help="Android icon name (default: ic_launcher)")
    parser.add_argument("--sizes", nargs="+", default=None,
                        help="Custom sizes for generic type (e.g., 48 72 96 or 100x200)")
    parser.add_argument("--adaptive-layer", choices=["foreground", "background"],
                        default=None, help="Generate adaptive icon layer")
    parser.add_argument("--remove-bg", action="store_true",
                        help="Remove background before processing")
    parser.add_argument("--bg-method",
                        choices=["auto", "rmbg", "rmbg-briaai", "rmbg-u2netp", "magick"],
                        default="auto", help="Background removal method (default: auto)")
    parser.add_argument("--bg-fuzz", type=int, default=10,
                        help="Fuzz %% for magick bg removal (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    src = Path(args.source)
    if not src.exists():
        print(f"Error: Source file not found: {src}", file=sys.stderr)
        sys.exit(1)

    if not check_imagemagick():
        print("Error: ImageMagick not found. Install: brew install imagemagick", file=sys.stderr)
        sys.exit(1)

    # Remove background if requested (before any resizing)
    if args.remove_bg:
        bg_out = src.parent / f"{src.stem}_nobg.png"
        if args.verbose:
            print("[Removing background before processing...]")
        bg_result = remove_background(
            src=str(src), dst=str(bg_out),
            method=args.bg_method, fuzz=args.bg_fuzz, verbose=args.verbose,
        )
        if bg_result["status"] == "success":
            src = bg_out
            if args.verbose:
                print(f"[Background removed] Using: {src}\n")
        else:
            print(f"Warning: Background removal failed: {bg_result['error']}", file=sys.stderr)

    # Determine platforms
    if args.platform == "auto":
        platforms = detect_project_type(args.project_dir)
    elif args.platform == "all":
        platforms = ["android", "ios"]
    else:
        platforms = [args.platform]

    if args.verbose:
        print(f"[Source] {src}")
        print(f"[Platforms] {', '.join(platforms)}")
        print(f"[Asset Type] {args.type}")
        print()

    all_outputs = []

    if args.type == "generic" and args.sizes:
        out_dir = args.output_dir or "./assets"
        all_outputs = process_generic(src, out_dir, args.sizes, verbose=args.verbose)

    elif args.type == "icon":
        for platform in platforms:
            if args.adaptive_layer:
                res_dir = get_android_res_dir(args.project_dir)
                all_outputs.extend(
                    process_android_adaptive(src, res_dir, args.adaptive_layer, args.verbose)
                )
            elif platform == "flutter":
                all_outputs.extend(process_flutter_icons(src, args.project_dir, args.verbose))
            elif platform == "react-native":
                all_outputs.extend(process_rn_icons(src, args.project_dir, verbose=args.verbose))
            elif platform == "android":
                res_dir = get_android_res_dir(args.project_dir)
                all_outputs.extend(
                    process_android_icons(src, res_dir, args.icon_name, args.verbose)
                )
            elif platform == "ios":
                ios_dir = get_ios_assets_dir(args.project_dir)
                all_outputs.extend(process_ios_icons(src, ios_dir, args.verbose))

    elif args.type == "splash":
        all_outputs = process_splash_screens(
            src, args.project_dir, platforms, args.verbose
        )

    elif args.type == "feature":
        out_dir = args.output_dir or "./assets"
        all_outputs = process_generic(
            src, out_dir, ["1024x500", "512x512"], "feature", args.verbose
        )

    print(f"\nProcessed {len(all_outputs)} assets.")
    for o in all_outputs:
        print(f"  {o}")


if __name__ == "__main__":
    main()
