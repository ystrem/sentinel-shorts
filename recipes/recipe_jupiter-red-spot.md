# 📋 Recipe: Jupiter's Great Red Spot (1665)

> **Output:** `shorts_jupiter-red-spot.mp4` | 3.3 MB | 7s | 1080×1920 | 3926 kbps

---

## 1. 📸 Background Image

| Param | Value |
|-------|-------|
| **Source** | NASA APOD |
| **Date** | 2026-04-16 |
| **Title** | South Celestial Tree |
| **URL** | https://apod.nasa.gov/apod/ap260416.html |
| **Processing** | Scale+center-crop to fill 1080×1920 portrait |
| **Aspect fix** | `scale=force_original_aspect_ratio=increase,crop=1080:1920` |

## 2. 🎙️ Narration (TTS)

| Param | Value |
|-------|-------|
| **Engine** | Qwen3 TTS (v2.1.0) |
| **Model** | `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` |
| **Voice** | `narrator` |
| **Language** | `english` |
| **Speed** | 1.0 |
| **Temperature** | 0.9 |
| **Duration** | 7.0s |
| **Server** | http://localhost:8050 (Docker, GPU P40) |
| **Inference** | ~30s generation on Tesla P40 |

**Narration text:**
```
Jupiter's Great Red Spot is a storm larger than Earth that has been raging for at least three hundred and fifty years.
```

## 3. 📝 Text Overlays

| # | Start | End | Text | Font Size | Y Position | Notes |
|---|-------|-----|------|-----------|------------|-------|
| 1 | 0.5s | 5.0s | `Jupiters Great Red Spot` | 48px | 780 | Title (apostrophe removed for FFmpeg compat) |
| 2 | 1.5s | 5.0s | `1665` | 64px | 870 | Year |
| 3 | 3.0s | 9.5s | `A storm bigger than Earth` | 28px | 1000 | Subtitle |

**Style parameters (all segments):**
- Color: `white` (full opacity with fade)
- Alpha fade: 0.4s fade-in, 0.4s fade-out per segment
- Drop shadow: `black`, 2px offset
- Horizontal position: centered `(w-text_w)/2`
- Enable: `between(t,start,end)`
- Font: `DejaVuSans.ttf` (system)

## 4. 🎞️ Video Composition

| Layer | Element | Filter |
|-------|---------|--------|
| 1 (bottom) | APOD background | `scale + crop + zoompan` (Ken Burns 1.0→1.15) |
| 2 | Dark gradient overlay | `geq` alpha gradient (transparent top → 100% bottom) |
| 3 | Text | `drawtext` with fade animation |
| 4 (top) | TTS audio | `afade` out at 1.5s before end |

**Full FFmpeg filter complex:**
```
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,
zoompan=z='min(1+0.15*on/300,1.15)':d=300:
x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':
s=1080x1920:fps=30[bg];

[1:v]loop=loop=300:size=1,format=rgba[grad];

[bg][grad]overlay=0:0[base];

[base]drawtext=...text filters...[outv];

[2:a]afade=t=out:st=5.5:d=1.5[aud]
```

## 5. ⚙️ Encoding

| Param | Value |
|-------|-------|
| Codec | H.264 (libx264) |
| CRF | 18 (high quality) |
| Preset | medium |
| Pixel format | yuv420p |
| Audio codec | AAC, 128 kbps, mono |
| FPS | 30 |
| Duration | 7s |
| Total frames | ~208 |

---

*Generated: 2026-05-04 | Sentinel Shorts Pipeline v1*
