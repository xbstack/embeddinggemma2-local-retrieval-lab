"""Create minimal synthetic multimodal fixtures. NOT a recognition benchmark."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "fixtures" / "multimodal-synthetic"
OUT.mkdir(parents=True, exist_ok=True)
side = 320
cases = [
    ("red-square", "A bright red square on a white background"),
    ("blue-circle", "A blue circle on a white background"),
]
for key, description in cases:
    im = Image.new("RGB", (side, side), "white")
    draw = ImageDraw.Draw(im)
    if key == "red-square":
        draw.rectangle((75, 75, 245, 245), fill=(229, 30, 38))
    else:
        draw.ellipse((75, 75, 245, 245), fill=(26, 80, 230))
    im.save(OUT / f"{key}.png")

audio = []
if shutil.which("say") and shutil.which("ffmpeg"):
    for key, description in cases:
        aiff = OUT / f"{key}.aiff"
        wav = OUT / f"{key}.wav"
        subprocess.run(["say", "-v", "Samantha", "-o", str(aiff), description],
                       check=True, timeout=25)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(aiff),
                        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
                        str(wav)], check=True, timeout=25)
        aiff.unlink(missing_ok=True)
        audio.append(wav.name)
manifest = {
    "status": "synthetic_fixtures_only",
    "created_by": "Pillow geometric drawings + macOS speech synthesis (Samantha)",
    "labels": [
        {"id": key, "text": desc, "image": f"{key}.png",
         "speech": f"{key}.wav" if f"{key}.wav" in audio else None}
        for key, desc in cases
    ],
    "no_claim": "These assets are not representative real-world image/audio retrieval samples.",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"images":len(cases),"audio":len(audio),
                  "paths":[str(OUT / x) for x in audio]}))
