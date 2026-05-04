#!/usr/bin/env python3
"""
Batch generate 4 HISTORY Shorts.
Facts: footprints-moon, first-star-map, neil-armstrong-quote, first-photo-from-space
"""

import subprocess, json, sys, time, requests
from pathlib import Path

REPO = Path(__file__).parent.parent
OUTDIR = REPO / "output" / "cinematic"
TTS_URL = "http://localhost:8050/generate"
CONTAINER = "sentinel-media-factory-tts-server-1"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SHORTS = [
    {
        "id": "footprints-moon",
        "image": "apod_2026-04-29.jpg",  # The Moon, Venus, and the Pleiades
        "narration": "The footprints left by Apollo astronauts on the Moon will remain for at least ten million years. There is no wind or water to erase them.",
        "segments": [
            (0.5, 5.0, "Footprints on the Moon", 48, "(w-text_w)/2", 780),
            (1.5, 5.0, "1969", 64, "(w-text_w)/2", 870),
            (3.0, 9.5, "They'll last millions of years", 28, "(w-text_w)/2", 1000),
        ],
    },
    {
        "id": "first-star-map",
        "image": "apod_2026-04-27.jpg",  # Comet R3 PanSTARRS Behind Satellite Trails
        "narration": "The Nebra Sky Disk, dated to sixteen hundred BC, is the oldest known depiction of the cosmos. A bronze disk with the Sun, Moon, and stars.",
        "segments": [
            (0.5, 5.0, "Oldest Star Map", 48, "(w-text_w)/2", 780),
            (1.5, 5.0, "1600 BC", 64, "(w-text_w)/2", 870),
            (3.0, 9.5, "Nebra Sky Disk", 28, "(w-text_w)/2", 1000),
        ],
    },
    {
        "id": "neil-armstrong",
        "image": "apod_2026-04-28.jpg",  # CG 30: Cometary Globules
        "narration": "Neil Armstrong's famous one small step quote was improvised. He said: That is one small step for man, one giant leap for mankind.",
        "segments": [
            (0.5, 5.0, "One Small Step", 48, "(w-text_w)/2", 780),
            (1.5, 5.0, "1969", 64, "(w-text_w)/2", 870),
            (3.0, 9.5, "First words on the Moon", 28, "(w-text_w)/2", 1000),
        ],
    },
    {
        "id": "first-photo-space",
        "image": "apod_2026-05-01.png",  # Markarian's Chain
        "narration": "The first photograph of Earth from space was taken in nineteen forty six by a camera mounted on a captured German V two rocket at one hundred and five kilometers altitude.",
        "segments": [
            (0.5, 5.0, "First Photo From Space", 42, "(w-text_w)/2", 780),
            (1.5, 5.0, "1946", 64, "(w-text_w)/2", 870),
            (3.0, 9.5, "A V-2 rocket captured this", 28, "(w-text_w)/2", 1000),
        ],
    },
]


def mk_gradient(gd):
    gd.mkdir(parents=True, exist_ok=True)
    gp = gd / "gradient_full.png"
    if not gp.exists():
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"color=c=#000000:s=1080x1920:d=1:r=1",
            "-vf","format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255-255*(Y/1920)'",
            "-frames:v","1","-c:v","png",str(gp)], capture_output=True, timeout=30)
    return gp

def gen_tts(text, out):
    print(f"  🎙️ Generating TTS...")
    r = requests.post(TTS_URL, json={"text":text,"language":"english","voice_preset":"narrator","speed":1.0,"temperature":0.9}, timeout=120)
    r.raise_for_status()
    d = r.json()
    subprocess.run(["docker","cp",f"{CONTAINER}:{d['file_path']}",str(out)], capture_output=True, timeout=30)
    print(f"    ✅ {d['duration']:.1f}s → {out.name}")
    return d["duration"]

def render(img, grad, audio, segs, out):
    dur, fps, w, h = 10, 30, 1080, 1920
    tf = dur * fps
    zoom = (f"scale=w={w}:h={h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},"
            f"zoompan=z='min(1+0.15*on/{tf},1.15)':d={tf}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}")
    tfs = []
    for s,e,t,fs,x,y in segs:
        fd = min(0.4,(e-s)/5)
        st = t.replace("'","’").replace("%","%%")
        al = f"if(lte(t,{s}+{fd}),(t-{s})/{fd},if(gte(t,{e}-{fd}),({e}-t)/{fd},1))"
        tfs.append(f"drawtext=text='{st}':fontfile={FONT}:fontsize={fs}:fontcolor=white:alpha='{al}':x={x}:y={y}:shadowcolor=black:shadowx=2:shadowy=2:enable='between(t,{s},{e})'")
    fc = ";".join([
        f"[0:v]{zoom}[bg]",
        f"[1:v]loop=loop={tf}:size=1,format=rgba[grad]",
        "[bg][grad]overlay=0:0[base]",
        f"[base]{','.join(tfs)}[outv]",
        f"[2:a]afade=t=out:st={dur-1.5}:d=1.5[aud]",
    ])
    cmd = ["ffmpeg","-y","-loop","1","-i",str(img),"-i",str(grad),"-i",str(audio),
        "-filter_complex",fc,"-map","[outv]","-map","[aud]","-shortest",
        "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-r","30","-t","10","-movflags","+faststart",str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if out.exists():
        print(f"  ✅ {out.name} ({out.stat().st_size/1e6:.1f} MB)")
        return True
    print(f"  ❌ FFmpeg error:\n{r.stderr.strip()[-200:]}")
    return False

def main():
    print("🚀 History Shorts × 4\n")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    grad = mk_gradient(OUTDIR / ".gradients")
    imgs = REPO / "data" / "images"
    ok = 0
    for s in SHORTS:
        print(f"── {s['id']} {'─'*30}")
        ip = imgs / s["image"]
        if not ip.exists():
            print(f"  ❌ Missing: {s['image']}")
            continue
        ap = OUTDIR / f"tts_{s['id']}.wav"
        if not ap.exists():
            try: gen_tts(s["narration"], ap)
            except Exception as e: print(f"  ❌ TTS: {e}"); continue
        else: print(f"  🎙️ Cached: {ap.name}")
        op = OUTDIR / f"shorts_{s['id']}.mp4"
        if render(ip, grad, ap, s["segments"], op): ok += 1
    print(f"\n✅ {ok}/{len(SHORTS)} videos")

if __name__ == "__main__":
    main()
