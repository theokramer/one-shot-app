#!/usr/bin/env python3
"""Assemble a one-shot demo video (and a README GIF) from a storyboard.

    make_demo.py storyboard.json                    # → out.mp4 (+ out.gif if "gif" is set)
    make_demo.py storyboard.json --readme README.md # also put the GIF between <!-- demo:start/end -->

storyboard.json (paths are relative to the storyboard file):
{
  "size": [1920, 1080], "fps": 30, "out": "oneshot-demo.mp4",
  "music": "music.mp3",                       # optional; silent track otherwise
  "gif": {"out": "demo.gif", "width": 900, "fps": 12, "max_mb": 9, "from": 0, "seconds": 22},
  "readme": {"gif_path": "docs/demo.gif", "video_url": "https://x.com/...", "alt": "one-shot run"},
  "segments": [
    {"type": "card", "text": "I pitched one app idea", "sub": "and walked away", "dur": 2.5},
    {"type": "clip", "file": "intro.mov", "start": 0, "end": 60, "speed": 2, "caption": "Pitch + a few clicks"},
    {"type": "timelapse", "dir": "frames", "seconds": 18, "caption": "Then it worked alone", "clock": true},
    {"type": "clip", "file": "sim.mp4", "caption": "The app it built", "fit": "contain"},
    {"type": "image", "file": "asc.png", "dur": 3, "caption": "Ready for review"},
    {"type": "card", "text": "Free Claude Code skill", "sub": "github.com/<you>/one-shot-app", "dur": 3}
  ]
}
Needs ffmpeg and Pillow. Captions, clock and cards are drawn locally (no AI imagery).
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

FONTS = ["/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Helvetica.ttc",
         "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]
BG, INK, ACCENT = (12, 12, 14), (245, 245, 247), (255, 214, 10)


def font(size, bold=True):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size, index=1 if (bold and f.endswith(".ttc")) else 0)
        except OSError:
            continue
    return ImageFont.load_default()


def ff(*args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("ffmpeg failed:\n" + r.stderr[-2000:])


def caption_layer(size, text, clock=None):
    """Transparent PNG with a bottom caption pill and an optional top-right clock."""
    W, H = size
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if text:
        f = font(int(H * 0.045))
        tw, th = d.textbbox((0, 0), text, font=f)[2:]
        pad = int(H * 0.022)
        x, y = (W - tw) // 2, H - th - int(H * 0.09)
        d.rounded_rectangle((x - pad * 1.6, y - pad, x + tw + pad * 1.6, y + th + pad * 1.3), radius=pad * 1.4,
                            fill=(0, 0, 0, 190))
        d.text((x, y), text, font=f, fill=INK)
    if clock:
        f = font(int(H * 0.04))
        tw, th = d.textbbox((0, 0), clock, font=f)[2:]
        x, y = W - tw - int(W * 0.04), int(H * 0.05)
        d.rounded_rectangle((x - 22, y - 14, x + tw + 22, y + th + 18), radius=18, fill=(0, 0, 0, 190))
        d.text((x, y), clock, font=f, fill=ACCENT)
    return im


def fit(img, size, mode="contain"):
    W, H = size
    img = img.convert("RGB")
    r = (min if mode == "contain" else max)(W / img.width, H / img.height)
    img = img.resize((max(1, int(img.width * r)), max(1, int(img.height * r))), Image.LANCZOS)
    canvas = Image.new("RGB", size, BG)
    canvas.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
    return canvas


def card(seg, size, out, fps, tmp):
    W, H = size
    im = Image.new("RGB", size, BG)
    d = ImageDraw.Draw(im)
    f1, f2 = font(int(H * 0.085)), font(int(H * 0.042), bold=False)
    t, s = seg.get("text", ""), seg.get("sub", "")
    tw, th = d.textbbox((0, 0), t, font=f1)[2:]
    d.text(((W - tw) // 2, H // 2 - th - (10 if s else -th // 2)), t, font=f1, fill=INK)
    if s:
        sw, _ = d.textbbox((0, 0), s, font=f2)[2:]
        d.text(((W - sw) // 2, H // 2 + 24), s, font=f2, fill=ACCENT)
    p = tmp / "card.png"
    im.save(p)
    still(p, seg.get("dur", 2.5), out, fps)


def still(png, dur, out, fps):
    ff("-loop", 1, "-t", dur, "-i", png, "-f", "lavfi", "-t", dur, "-i", "anullsrc=r=44100:cl=stereo",
       "-r", fps, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out)


def image(seg, base, size, out, fps, tmp):
    im = fit(Image.open(base / seg["file"]), size, seg.get("fit", "contain"))
    im.paste(cap := caption_layer(size, seg.get("caption", "")), (0, 0), cap)
    p = tmp / "img.png"
    im.save(p)
    still(p, seg.get("dur", 3), out, fps)


def clip(seg, base, size, out, fps, tmp):
    W, H = size
    src = base / seg["file"]
    sp = float(seg.get("speed", 1))
    cap = tmp / "cap.png"
    caption_layer(size, seg.get("caption", "")).save(cap)
    trim = []
    if "start" in seg:
        trim += ["-ss", seg["start"]]
    if "end" in seg:
        trim += ["-to", seg["end"]]
    scale = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0c0c0e"
             if seg.get("fit", "contain") == "contain" else
             f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}")
    ff(*trim, "-i", src, "-i", cap, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
       "-filter_complex", f"[0:v]setpts=PTS/{sp},{scale},fps={fps}[v];[v][1:v]overlay=0:0[o]",
       "-map", "[o]", "-map", "2:a", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", out)


def timelapse(seg, base, size, out, fps, tmp):
    frames = sorted((base / seg["dir"]).glob("*.jpg"), key=lambda p: p.stem)
    if not frames:
        raise SystemExit(f"no frames in {seg['dir']}")
    n = max(2, int(float(seg.get("seconds", 15)) * fps))
    pick = [frames[round(i * (len(frames) - 1) / (n - 1))] for i in range(n)] if len(frames) > n else frames
    t0 = int(pick[0].stem) if pick[0].stem.isdigit() else None
    seq = tmp / "tl"
    seq.mkdir()
    for i, f in enumerate(pick):
        im = fit(Image.open(f), size, seg.get("fit", "contain"))
        clock = None
        if seg.get("clock", True) and t0 is not None and f.stem.isdigit():
            m = (int(f.stem) - t0) // 60
            clock = f"+{m // 60}:{m % 60:02d} h"
        layer = caption_layer(size, seg.get("caption", ""), clock)
        im.paste(layer, (0, 0), layer)
        im.save(seq / f"{i:06d}.jpg", quality=90)
    dur = len(pick) / fps
    ff("-framerate", fps, "-i", seq / "%06d.jpg", "-f", "lavfi", "-t", dur, "-i", "anullsrc=r=44100:cl=stereo",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", fps, "-c:a", "aac", "-shortest", out)


def duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def make_gif(video, g, base):
    out = base / g.get("out", "demo.gif")
    width, gfps, max_mb = int(g.get("width", 900)), int(g.get("fps", 12)), float(g.get("max_mb", 9))
    span = ["-ss", g.get("from", 0)] + (["-t", g["seconds"]] if g.get("seconds") else [])
    while True:
        vf = f"fps={gfps},scale={width}:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4"
        ff(*span, "-i", video, "-filter_complex", vf, "-loop", 0, out)
        mb = out.stat().st_size / 1e6
        if mb <= max_mb or width <= 480:
            print(f"gif {out} {mb:.1f} MB at {width}px")
            return out
        width = int(width * 0.85)


def update_readme(readme, r, gif_name):
    p = pathlib.Path(readme)
    s = p.read_text()
    a, b = "<!-- demo:start -->", "<!-- demo:end -->"
    if a not in s or b not in s:
        raise SystemExit("README has no <!-- demo:start --> / <!-- demo:end --> markers")
    block = f'<p align="center"><img src="{r.get("gif_path", gif_name)}" width="720" alt="{r.get("alt", "demo")}"></p>'
    if r.get("video_url"):
        block += f'\n<p align="center"><a href="{r["video_url"]}">Watch the full run</a></p>'
    s = s[:s.index(a) + len(a)] + "\n" + block + "\n" + s[s.index(b):]
    p.write_text(s)
    print("README updated")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg missing: brew install ffmpeg")
    sb_path = pathlib.Path(sys.argv[1]).resolve()
    base = sb_path.parent
    sb = json.loads(sb_path.read_text())
    size, fps = tuple(sb.get("size", [1920, 1080])), int(sb.get("fps", 30))
    out = base / sb.get("out", "oneshot-demo.mp4")
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        parts = []
        for i, seg in enumerate(sb["segments"]):
            stmp = tmp / f"s{i}"
            stmp.mkdir()
            part = tmp / f"part{i:02d}.mp4"
            {"card": lambda: card(seg, size, part, fps, stmp),
             "image": lambda: image(seg, base, size, part, fps, stmp),
             "clip": lambda: clip(seg, base, size, part, fps, stmp),
             "timelapse": lambda: timelapse(seg, base, size, part, fps, stmp)}[seg["type"]]()
            parts.append(part)
            print(f"segment {i + 1}/{len(sb['segments'])} {seg['type']} {duration(part):.1f}s")
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        joined = tmp / "joined.mp4"
        ff("-f", "concat", "-safe", 0, "-i", lst, "-c", "copy", joined)
        total = duration(joined)
        if sb.get("music"):
            ff("-i", joined, "-i", base / sb["music"], "-filter_complex",
               f"[1:a]atrim=0:{total},afade=t=in:d=0.8,afade=t=out:st={max(0, total - 2)}:d=2,volume=0.9[m]",
               "-map", "0:v", "-map", "[m]", "-c:v", "copy", "-c:a", "aac", "-shortest", out)
        else:
            shutil.copy(joined, out)
    print(f"video {out} {duration(out):.1f}s")
    if sb.get("gif"):
        g = make_gif(out, sb["gif"], base)
        if "--readme" in sys.argv:
            update_readme(sys.argv[sys.argv.index("--readme") + 1], sb.get("readme", {}), g.name)


if __name__ == "__main__":
    main()
