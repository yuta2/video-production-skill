#!/usr/bin/env python3
"""
Burn hand-written Chinese subtitles onto slides using ImageMagick caption + composite.

This is the ONLY reliable method for CJK hand-written subtitles on macOS.
ffmpeg drawtext / libass / PIL FreeType all have compatibility issues.

Usage:
    python3 burn_captions.py [project_dir]

Workflow:
    1. Reads SRT + narration.json + slide audio durations
    2. Maps SRT cues to slides
    3. Uses ImageMagick caption: to render subtitle text onto each slide
    4. Replaces original slides/ with subtitled versions

Dependencies: ImageMagick (magick), ffprobe
"""

import json, subprocess, os, re, glob, pathlib, shutil, sys

PROJ = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path.cwd()

# Preferred font for hand-written Chinese
FONT = os.environ.get("SUB_FONT", "/Users/yuta2/Library/Fonts/ChenYuluoyan-Thin.ttf")
FONT_SIZE = os.environ.get("SUB_FS", "26")
MAX_WIDTH = os.environ.get("SUB_WIDTH", "1500")
MARGIN_BOTTOM = os.environ.get("SUB_MARGIN", "80")

# ── Parse SRT ──
srt_path = PROJ / "subtitles_aligned.srt"
if not srt_path.exists():
    print(f"ERROR: {srt_path} not found")
    sys.exit(1)

cues = []
with open(srt_path) as f:
    srt_content = f.read()

for block in srt_content.strip().split('\n\n'):
    lines = block.strip().split('\n')
    if len(lines) < 3:
        continue
    m = re.match(
        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
        lines[1]
    )
    if not m:
        continue
    start = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/1000
    end = int(m.group(5))*3600 + int(m.group(6))*60 + int(m.group(7)) + int(m.group(8))/1000
    cues.append((start, end, ''.join(lines[2:])))

print(f"Parsed {len(cues)} SRT cues")

# ── Get slide durations from audio ──
audio_files = sorted(glob.glob(str(PROJ / "audio" / "slide_*.mp3")))
if not audio_files:
    print("ERROR: no audio files found")
    sys.exit(1)

slide_dur = []
for af in audio_files:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", af],
        capture_output=True, text=True
    )
    slide_dur.append(float(r.stdout.strip()))

slide_start = [0.0]
for d in slide_dur[:-1]:
    slide_start.append(slide_start[-1] + d + 1.0)

# ── Map cues to slides ──
slide_texts = {i: [] for i in range(len(slide_dur))}
for start, end, text in cues:
    for i, ss in enumerate(slide_start):
        se = slide_start[i+1] if i+1 < len(slide_start) else ss + slide_dur[i] + 1.0
        if start >= ss - 0.1 and start < se:
            slide_texts[i].append(text)
            break

# ── Burn onto slides ──
slides_dir = PROJ / "slides"
if not slides_dir.exists():
    print(f"ERROR: {slides_dir} not found")
    sys.exit(1)

# Backup original slides
backup_dir = PROJ / "slides_clean"
if not backup_dir.exists():
    shutil.copytree(str(slides_dir), str(backup_dir))

print(f"Burning subtitles with font: {FONT}")

temp_text = "/tmp/sub_caption.txt"
temp_overlay = "/tmp/sub_overlay.png"

for i in range(len(slide_dur)):
    full_text = ' '.join(slide_texts[i])
    src = slides_dir / f"slide_{i+1:02d}.png"
    dst = slides_dir / f"slide_{i+1:02d}.png"  # overwrite

    with open(temp_text, 'w') as f:
        f.write(full_text)

    # Render caption
    subprocess.run([
        "magick",
        "-size", f"{MAX_WIDTH}x",
        "-font", FONT,
        "-pointsize", FONT_SIZE,
        "-fill", "white",
        "-background", "rgba(0,0,0,0.5)",
        "-gravity", "center",
        f"caption:@{temp_text}",
        temp_overlay
    ], capture_output=True, check=True)

    # Composite onto slide
    subprocess.run([
        "magick", str(src),
        temp_overlay,
        "-gravity", "south",
        "-geometry", f"+0+{MARGIN_BOTTOM}",
        "-composite",
        str(dst)
    ], capture_output=True, check=True)

    print(f"✅ slide_{i+1:02d}: {len(slide_texts[i])} cues")

os.remove(temp_text)
os.remove(temp_overlay)

print(f"\nDone. {len(slide_dur)} slides burned. Originals at {backup_dir}/")
print("Now run: node scripts/assemble.js [project_dir]")
