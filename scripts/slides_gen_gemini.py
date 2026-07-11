"""Gemini image generation for slides (storybook watercolor / blackboard styles).

Reads slides_prompts.json from the project directory, same format as slides_gen.py.

Usage:
  python slides_gen_gemini.py                      # generate all slides
  python slides_gen_gemini.py 3 7                  # regenerate only slides 3 and 7
  python slides_gen_gemini.py --dir my-proj --model gemini-3.1-flash-image
  python slides_gen_gemini.py --dir my-proj --style alice-watercolor

Models:
  gemini-3.1-flash-image      $0.045/img (recommended — good CJK)
  gemini-3.1-flash-lite-image $0.034/img (cheapest, CJK TBD)
  gemini-3-pro-image           $0.134/img (best quality)

Styles:
  blackboard    — hand-drawn professor board style (default)
  alice-watercolor — 小愛麗絲手繪水彩童話風

Output: slides_raw/slide_NN.png (1536x1024). Pad afterwards with `node pad_and_burn.js pad`.

Needs GEMINI_API_KEY (env var, or .env in the project directory).
"""

import os, sys, json, time, pathlib, base64
import requests

args = [a for a in sys.argv[1:]]
proj = "."
model = "gemini-3.1-flash-image"
style_name = "blackboard"

# Parse flags
i = 0
while i < len(args):
    if args[i] == "--dir":
        proj = args[i+1]; i += 2
    elif args[i] == "--model":
        model = args[i+1]; i += 2
    elif args[i] == "--style":
        style_name = args[i+1]; i += 2
    else:
        i += 1

PROJ = pathlib.Path(proj).resolve()

# Slide IDs (remaining positional args after stripping flags)
slide_ids = [int(x) for x in args if x.lstrip("-").isdigit()]

def load_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    envf = PROJ / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ERROR: GEMINI_API_KEY not set (env var or .env in project dir)")

API_KEY = load_key()
OUT = PROJ / "slides_raw"
OUT.mkdir(exist_ok=True)

# ── Style profiles ──

STYLE_PROFILES = {
    "blackboard": {
        "prefix": "白底手繪教學風，教授板書風格。",
        "suffix": "所有中文字必須完全正確、清楚可讀、不可有亂碼或錯字。不要出現任何未指定的文字或圖案。FORBIDDEN: any text besides the header and subtitle. No narration text, no poetry, no dialogue, no captions anywhere on the image.",
        "aspect_ratio": "3:2",
    },
    "alice-watercolor": {
        "prefix": (
            "Cozy hand-drawn watercolor storybook infographic style, warm parchment paper background, "
            "soft brown hand-drawn lines, warm amber and cream palette with storybook blue accents. "
            "Lower left corner: cute chibi Xiao Alice (小愛麗絲) character with gentle smile holding a quill pen. "
            "Clear, readable Traditional Chinese text in a storybook layout. "
        ),
        "suffix": "所有中文字必須完全正確、清楚可讀、不可有亂碼或錯字。不要出現任何未指定的文字或圖案。",
        "aspect_ratio": "3:2",
    },
}

style = STYLE_PROFILES.get(style_name, STYLE_PROFILES["blackboard"])

# ── Load prompts ──

spec = json.loads((PROJ / "slides_prompts.json").read_text(encoding="utf-8"))
if isinstance(spec, dict):
    shared = spec.get("style", "")
    prompts = [shared + "\n" + s for s in spec["slides"]]
else:
    prompts = list(spec)

# ── Generate ──

URL = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"

def gen(idx):
    """idx is 1-based."""
    out = OUT / f"slide_{idx:02d}.png"
    t0 = time.time()
    print(f"[{idx}] gen ({model}, {style_name})...", flush=True)

    full_prompt = style["prefix"] + "\n" + prompts[idx-1] + "\n" + style["suffix"]

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
            "imageConfig": {"aspectRatio": style["aspect_ratio"]}
        }
    }

    try:
        resp = requests.post(URL, json=payload, timeout=180)
        data = resp.json()

        if "candidates" not in data:
            err = data.get("error", data)
            print(f"[{idx}] FAIL: {json.dumps(err, ensure_ascii=False)[:300]}", flush=True)
            return

        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                out.write_bytes(img_data)
                elapsed = time.time() - t0
                cost_est = {"gemini-3.1-flash-image": 0.045, "gemini-3.1-flash-lite-image": 0.034, "gemini-3-pro-image": 0.134}.get(model, 0.045)
                print(f"[{idx}] -> {out} ({len(img_data)//1024}KB) {elapsed:.0f}s ~${cost_est:.3f}", flush=True)

                # Log cost
                log_cost(idx, model, cost_est, elapsed)
                return
            elif "text" in part:
                txt = part["text"][:200]
                if txt.strip():
                    print(f"[{idx}] text: {txt}", flush=True)

        print(f"[{idx}] WARN: no image in response", flush=True)

    except Exception as e:
        print(f"[{idx}] FAIL: {e}", flush=True)


def log_cost(idx, model_name, cost, elapsed):
    """Append cost entry to cost log."""
    log_path = PROJ / "cost_log.jsonl"
    entry = json.dumps({
        "slide": idx,
        "model": model_name,
        "provider": "gemini",
        "cost_usd": cost,
        "elapsed_s": round(elapsed, 1),
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    with open(log_path, "a") as f:
        f.write(entry + "\n")


if __name__ == "__main__":
    ids = slide_ids or list(range(1, len(prompts) + 1))
    for i in ids:
        gen(i)

    # Summary
    log_path = PROJ / "cost_log.jsonl"
    if log_path.exists():
        total = 0
        with open(log_path) as f:
            for line in f:
                total += json.loads(line).get("cost_usd", 0)
        print(f"\n💰 Total image cost: ${total:.3f} ({len(ids)} slides, {model})")
