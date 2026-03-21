# Platform Asset Specifications

## Android

### App Icons (Launcher)

| Density | Size (px) | Directory |
|---------|-----------|-----------|
| mdpi | 48x48 | `mipmap-mdpi/ic_launcher.png` |
| hdpi | 72x72 | `mipmap-hdpi/ic_launcher.png` |
| xhdpi | 96x96 | `mipmap-xhdpi/ic_launcher.png` |
| xxhdpi | 144x144 | `mipmap-xxhdpi/ic_launcher.png` |
| xxxhdpi | 192x192 | `mipmap-xxxhdpi/ic_launcher.png` |
| Play Store | 512x512 | `ic_launcher-playstore.png` |

### Adaptive Icons (Android 8+)

Foreground/background layers at 108dp (72dp visible, 18dp padding):

| Density | Layer Size | Files |
|---------|------------|-------|
| mdpi | 108x108 | `ic_launcher_foreground.png`, `ic_launcher_background.png` |
| hdpi | 162x162 | Same naming per density |
| xhdpi | 216x216 | |
| xxhdpi | 324x324 | |
| xxxhdpi | 432x432 | |

XML definition: `mipmap-anydpi-v26/ic_launcher.xml`
```xml
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
```

### Feature Graphic
- Google Play: 1024x500 px

### Splash Screens
| Density | Size |
|---------|------|
| mdpi | 320x480 |
| hdpi | 480x800 |
| xhdpi | 720x1280 |
| xxhdpi | 1080x1920 |
| xxxhdpi | 1440x2560 |

---

## iOS

### App Icons (AppIcon.appiconset)

| Context | Size | Scale | Pixels |
|---------|------|-------|--------|
| Notification | 20pt | 1x/2x/3x | 20/40/60 |
| Settings | 29pt | 1x/2x/3x | 29/58/87 |
| Spotlight | 40pt | 1x/2x/3x | 40/80/120 |
| iPhone | 60pt | 2x/3x | 120/180 |
| iPad | 76pt | 1x/2x | 76/152 |
| iPad Pro | 83.5pt | 2x | 167 |
| App Store | 1024pt | 1x | 1024 |

**Requirements:** PNG, no alpha/transparency, sRGB color space.

### Splash (Launch Images)
Use LaunchScreen.storyboard preferred. If image-based:
- `Default@2x~universal~anyany.png` (2732x2732)
- `Default@2x~universal~comany.png` (1278x2732)

---

## Flutter

Uses Android + iOS specs above, plus:

### Web Icons (`web/icons/`)
| File | Size |
|------|------|
| `Icon-192.png` | 192x192 |
| `Icon-512.png` | 512x512 |
| `Icon-maskable-192.png` | 192x192 |
| `Icon-maskable-512.png` | 512x512 |
| `favicon.png` | 16x16 |

### In-App Assets (`assets/images/`)
Convention: `1.0x/`, `2.0x/`, `3.0x/` subdirectories.

---

## React Native

Uses Android + iOS specs above.

### In-App Images
Name convention: `image.png`, `image@2x.png`, `image@3x.png`
Base size: design at 1x, provide 2x and 3x variants.

---

## Recommended Source Sizes

| Asset Type | Min Source | Recommended |
|------------|-----------|-------------|
| App Icon | 512x512 | 1024x1024 |
| Splash Screen | 1080x1920 | 1440x2560 |
| Feature Graphic | 1024x500 | 1024x500 |
| In-App Icon | 96x96 | 192x192 |
| Illustration | 1080x1080 | 2048x2048 |
