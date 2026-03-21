# Asset Generation Workflow

## End-to-End Process

```
1. User request → 2. Detect project → 3. Generate image → 4. Process sizes → 5. Deploy to dirs
```

### Step 1: Parse Request

Identify from user message:
- **Concept**: What the asset represents
- **Asset type**: icon, splash, feature, illustration, in-app-icon
- **Platform**: Explicit or auto-detected
- **Style preferences**: Colors, style, mood (pass as custom prompt if specific)

### Step 2: Detect Project Type

```bash
python scripts/process_assets.py source.png --platform auto --project-dir .
```

Detection logic:
- `pubspec.yaml` → Flutter
- `package.json` + `react-native` dep → React Native
- `AndroidManifest.xml` → Android
- `*.xcodeproj` / `*.xcworkspace` → iOS

### Step 3: Generate Base Image

```bash
# Standard generation
python scripts/generate_asset.py "music player" --type icon -o /tmp/icon_base.png -v

# Custom prompt for specific requirements
python scripts/generate_asset.py "music player" --type icon -o /tmp/icon_base.png \
    --prompt "A minimalist music note icon, gradient blue to purple, no text" -v

# Dry run to preview prompt
python scripts/generate_asset.py "music player" --type icon -o /tmp/icon.png --dry-run
```

Model priority: Nano Banana 2 (flash) → Nano Banana Pro (fallback).

### Step 4: Process to Platform Sizes

```bash
# Auto-detect project and process
python scripts/process_assets.py /tmp/icon_base.png --type icon -d /path/to/project -v

# Specific platform
python scripts/process_assets.py /tmp/icon_base.png --type icon -p android -d . -v

# Adaptive icon layers (Android)
python scripts/process_assets.py /tmp/fg.png --type icon --adaptive-layer foreground -d .
python scripts/process_assets.py /tmp/bg.png --type icon --adaptive-layer background -d .

# Splash screens
python scripts/process_assets.py /tmp/splash_base.png --type splash -d . -v

# Custom sizes
python scripts/process_assets.py /tmp/asset.png --type generic --sizes 48 72 96 144 192
```

### Step 5: Verify Output

After processing, verify assets exist in correct directories:
- Android: `app/src/main/res/mipmap-*/`
- iOS: `Assets.xcassets/AppIcon.appiconset/`
- Flutter: Both above + `web/icons/`
- React Native: Both Android + iOS above

## Common Scenarios

### New App Icon
```bash
python scripts/generate_asset.py "fitness tracker app" --type icon -o /tmp/icon.png -v
python scripts/process_assets.py /tmp/icon.png --type icon -d /path/to/project -p auto -v
```

### Replace Splash Screen
```bash
python scripts/generate_asset.py "fitness app loading" --type splash -o /tmp/splash.png -v
python scripts/process_assets.py /tmp/splash.png --type splash -d /path/to/project -v
```

### Generate Feature Graphic for Play Store
```bash
python scripts/generate_asset.py "fitness tracker showcase" --type feature \
    -o /tmp/feature.png -ar 16:9 -v
python scripts/process_assets.py /tmp/feature.png --type feature -o ./store-assets -v
```

### In-App Illustration
```bash
python scripts/generate_asset.py "empty inbox illustration" --type illustration \
    -o /tmp/empty_state.png -v
python scripts/process_assets.py /tmp/empty_state.png --type generic \
    --sizes 360x360 720x720 1080x1080 -o assets/images -v
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `GEMINI_API_KEY not found` | Set env var or add to `~/.claude/.env` |
| `google-genai not installed` | `pip install google-genai` |
| `ImageMagick not found` | `brew install imagemagick` (macOS) |
| Flash model fails | Auto-falls back to Pro; check API quota |
| Wrong project detected | Use `--platform` flag explicitly |
| Icons look blurry | Generate at higher `--size` (4K) |
