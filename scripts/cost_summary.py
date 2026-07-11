#!/usr/bin/env python3
"""Cost summary for video production. Reads cost_log.jsonl from project dir.

Usage:
  python scripts/cost_summary.py [project_dir]
"""

import sys, json, pathlib

proj = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
log = proj / "cost_log.jsonl"

if not log.exists():
    print("No cost_log.jsonl found.")
    sys.exit(0)

entries = []
with open(log) as f:
    for line in f:
        if line.strip():
            entries.append(json.loads(line))

if not entries:
    print("No entries.")
    sys.exit(0)

print(f"{'Slide':>6} {'Model':<32} {'Cost':>8} {'Time':>6}")
print("-" * 58)

total = 0
for e in entries:
    print(f"{e['slide']:>6} {e['model']:<32} ${e['cost_usd']:>7.3f} {e['elapsed_s']:>5.0f}s")
    total += e['cost_usd']

print("-" * 58)
print(f"{'TOTAL':>6} {'':32} ${total:>7.3f}")

# Estimate TTS cost (rough: ElevenLabs ~$0.015 per 1000 chars)
import os
narration = proj / "narration.json"
if narration.exists():
    text = narration.read_text()
    chars = len(text)
    tts_est = chars / 1000 * 0.015
    print(f"\n📝 TTS est: ~{chars} chars → ~${tts_est:.3f} (ElevenLabs)")
    total += tts_est

print(f"\n💰 Total estimated: ${total:.3f}")
