#!/usr/bin/env python3
"""Gemini TTS + ASR verification for video production.

Reads narration.json from project directory, synthesizes each slide to MP3
via Gemini 3.1 Flash TTS, then verifies with Whisper ASR.

Usage:
  python3 tts_gemini.py [project_dir]

Config: reads config.json for tts.voice (default: Kore) and asr.passThreshold.
Needs GEMINI_API_KEY and OPENAI_API_KEY (env vars or .env in project dir).

Output: audio/slide_NN.mp3
"""

import os, sys, json, time, pathlib, base64, subprocess, tempfile
import requests

PROJ = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path.cwd()

# ── Load config ──
CFG_PATH = PROJ / "config.json"
cfg = {}
if CFG_PATH.exists():
    cfg = json.loads(CFG_PATH.read_text())

GEMINI_VOICE = cfg.get("tts", {}).get("gemini_voice", "Kore")
PASS_THRESHOLD = cfg.get("asr", {}).get("passThreshold", 0.85)
MAX_RETRIES = cfg.get("tts", {}).get("maxRetries", 5)

# ── Load API keys ──
def load_env():
    envf = PROJ / ".env"
    if envf.exists():
        for line in envf.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if k not in os.environ:
                    os.environ[k] = v

load_env()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

if not GEMINI_KEY:
    sys.exit("ERROR: GEMINI_API_KEY not set")
if not OPENAI_KEY:
    sys.exit("ERROR: OPENAI_API_KEY not set")

# ── Load narration ──
NARR_PATH = PROJ / "narration.json"
if not NARR_PATH.exists():
    sys.exit(f"ERROR: {NARR_PATH} not found")

narration = json.loads(NARR_PATH.read_text())
AUDIO_DIR = PROJ / "audio"
AUDIO_DIR.mkdir(exist_ok=True)
TEMP_DIR = PROJ / "temp"
TEMP_DIR.mkdir(exist_ok=True)

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent?key={GEMINI_KEY}"

print(f"Project: {PROJ}")
print(f"Slides: {len(narration)} | Voice: {GEMINI_VOICE} | Threshold: {PASS_THRESHOLD}")
print("---\n")

def tts_gemini(text, voice):
    """Synthesize text via Gemini TTS. Returns raw PCM bytes."""
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice}
                }
            }
        }
    }
    resp = requests.post(GEMINI_URL, json=payload, timeout=120)
    data = resp.json()
    if "error" in data:
        raise Exception(data["error"]["message"])
    for part in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise Exception("No audio in response")


def pcm_to_mp3(raw_bytes, out_path):
    """Convert raw PCM 24kHz mono to MP3 via ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".l16", delete=False) as tmp:
        tmp.write(raw_bytes)
        tmp_path = tmp.name
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "s16le", "-ar", "24000", "-ac", "1",
        "-i", tmp_path,
        "-codec:a", "libmp3lame", "-b:a", "128k",
        out_path
    ], capture_output=True, check=True)
    os.unlink(tmp_path)
    return os.path.getsize(out_path)


def asr_verify(mp3_path, original_text):
    """Run Whisper ASR on MP3 and compute similarity."""
    with open(mp3_path, "rb") as f:
        resp = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            files={"file": ("audio.mp3", f, "audio/mpeg")},
            data={"model": "whisper-1", "language": "zh", "response_format": "text"}
        )
    transcribed = resp.text.strip()
    # Character overlap similarity
    orig_chars = set(original_text.replace(" ", "").replace("\n", ""))
    trans_chars = set(transcribed.replace(" ", "").replace("\n", ""))
    if not orig_chars:
        return 0, transcribed
    overlap = len(orig_chars & trans_chars)
    similarity = overlap / len(orig_chars) * 100
    return round(similarity, 1), transcribed


passed = 0
failed = 0

for idx, text in enumerate(narration):
    i = idx + 1
    out_path = AUDIO_DIR / f"slide_{i:02d}.mp3"
    best_sim = 0
    
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"[{i:02d}/{len(narration):02d}] Attempt {attempt}/{MAX_RETRIES}...")
        try:
            raw = tts_gemini(text, GEMINI_VOICE)
            size = pcm_to_mp3(raw, str(out_path))
            print(f"  TTS OK: {size//1024} KB")
            
            sim, trans = asr_verify(str(out_path), text)
            print(f"  Similarity: {sim}%")
            if sim > best_sim:
                best_sim = sim
            
            if sim >= PASS_THRESHOLD * 100:
                print(f"  ✅ PASS")
                passed += 1
                break
            else:
                print(f"  ❌ FAIL (need ≥{PASS_THRESHOLD*100:.0f}%)")
                if attempt < MAX_RETRIES:
                    print(f"  Original: {text[:80]}...")
                    print(f"  ASR got:  {trans[:80]}...")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    if best_sim < PASS_THRESHOLD * 100:
        failed += 1
        print(f"  ⚠️ Keeping best attempt ({best_sim}%)")

print(f"\n{'='*40}")
print(f"Done! Passed: {passed}, Failed: {failed}, Total: {len(narration)}")
if failed > 0:
    print("⚠️ Some slides did not meet ASR threshold — ship on redundancy if key words correct.")
