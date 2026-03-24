# mobile-assets-skills

Claude Code plugin for generating and processing mobile app assets (icons, splash screens, feature graphics, illustrations) using Nano Banana image models.

## Features

- **Image Generation** via Nano Banana 2 (flash) with automatic fallback to Nano Banana Pro
- **Background Removal** via rembg (AI-powered, BiRefNet model) with ImageMagick fallback — **enabled by default** for PNG output
- **Asset Types**: App icons, splash screens, feature graphics, illustrations, in-app icons
- **All Platforms**: Android, iOS, Flutter, React Native
- **Auto-Detection**: Detects project type from directory structure
- **Full Pipeline**: Generate -> remove background -> resize -> deploy to platform-specific directories
- **Android Adaptive Icons**: Separate foreground/background layer support
- **iOS Contents.json**: Auto-generated during icon processing

## Prerequisites

```bash
pip install google-genai          # Nano Banana API
brew install imagemagick           # Image processing
pip install "rembg[cpu]"            # AI background removal (BiRefNet)
export GEMINI_API_KEY="your-key"   # https://aistudio.google.com/apikey
```

## Installation

### As a Claude Code Plugin (recommended)

```bash
# Add marketplace and install
/plugin marketplace add tsnAnh/mobile-assets-skills
/plugin install mobile-assets-skills@latest
```

### As a Claude Code Skill (manual)

```bash
cp -r . ~/.claude/skills/mobile-assets-skills
```

### Project-specific

```bash
cp -r . .claude/skills/mobile-assets-skills
```

## Usage

### Generate an app icon (transparent by default)

```bash
python scripts/generate_asset.py "fitness tracker" -t icon -o /tmp/icon.png -v

# Keep original background (disable auto-removal)
python scripts/generate_asset.py "fitness tracker" -t icon -o /tmp/icon.png --no-remove-bg -v
```

### Process to all platform sizes

```bash
# Auto-detect project type
python scripts/process_assets.py /tmp/icon.png -t icon -d /path/to/project -v

# Specific platform
python scripts/process_assets.py /tmp/icon.png -t icon -p android -d . -v
```

### Generate splash screen

```bash
python scripts/generate_asset.py "app loading" -t splash -o /tmp/splash.png
python scripts/process_assets.py /tmp/splash.png -t splash -d . -v
```

### Android adaptive icon layers

```bash
python scripts/generate_asset.py "app foreground" -t icon -o /tmp/fg.png
python scripts/process_assets.py /tmp/fg.png -t icon --adaptive-layer foreground -d .
```

### Feature graphic for Play Store

```bash
python scripts/generate_asset.py "app showcase" -t feature -o /tmp/feature.png -ar 16:9
python scripts/process_assets.py /tmp/feature.png -t feature -o ./store-assets -v
```

### Remove background only (standalone)

```bash
python scripts/remove_bg.py input.png -o output.png -v              # birefnet (default)
python scripts/remove_bg.py input.png -o output.png --method u2net   # faster alternative
python scripts/remove_bg.py input.png -o output.png --method isnet   # general-use model
python scripts/remove_bg.py input.png -o output.png --method magick  # color-based, solid backgrounds only
```

## Structure

```
mobile-assets-skills/
├── .claude-plugin/
│   ├── plugin.json                       # Plugin manifest
│   └── marketplace.json                  # Marketplace catalog
├── skills/
│   └── mobile-assets/
│       └── SKILL.md                      # Skill definition (for Claude Code)
├── scripts/
│   ├── generate_asset.py                 # Nano Banana image generation
│   ├── process_assets.py                 # Resize & deploy to platform dirs
│   └── remove_bg.py                      # AI background removal
├── references/
│   ├── platform-asset-specs.md           # Android/iOS/Flutter/RN size specs
│   └── asset-workflow.md                 # End-to-end workflow guide
└── README.md
```

## Platform Output Directories

| Platform | Icons | Splash |
|----------|-------|--------|
| Android | `app/src/main/res/mipmap-*/` | `app/src/main/res/drawable-*/` |
| iOS | `Assets.xcassets/AppIcon.appiconset/` | `Assets.xcassets/LaunchImage.imageset/` |
| Flutter | Android + iOS + `web/icons/` | Android + iOS |
| React Native | Android + iOS | Android + iOS |

## License

MIT
