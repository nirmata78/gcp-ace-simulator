#!/usr/bin/env python3
"""Run the kit's build_video.build() unchanged, with Kokoro wrapped in a content-addressed cache and the course pronunciation map.
Editing one sentence re-synthesises one line; the shared kit script stays untouched."""
import argparse, hashlib, os, pathlib, sys
os.environ["KOKORO_REEXEC"] = "1"
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import numpy as np
import build_video as bv
from say import SAY
CACHE = pathlib.Path.home() / ".cache/ace-video/tts"; CACHE.mkdir(parents=True, exist_ok=True)
RealKokoro = bv.Kokoro
class Cached:
    def __init__(self, *a): self.a, self.k = a, None
    def create(self, text, voice, speed, lang):
        h = hashlib.sha1(f"{voice}|{speed}|{lang}|{text}".encode()).hexdigest()
        p = CACHE / f"{h}.npz"
        if p.exists():
            z = np.load(p); return z["a"], int(z["sr"])
        if self.k is None: self.k = RealKokoro(*self.a)
        audio, sr = self.k.create(text, voice=voice, speed=speed, lang=lang)
        tmp = p.with_suffix(f".{os.getpid()}.tmp.npz"); np.savez_compressed(tmp, a=audio.astype(np.float32), sr=sr); tmp.replace(p)
        return audio, sr
bv.Kokoro = Cached
bv.SAY = {**bv.SAY, **SAY}
ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("--frames"); ap.add_argument("--out")
a = ap.parse_args()
bv.build(pathlib.Path(a.script), pathlib.Path(a.frames), pathlib.Path(a.out), "burn", 0, 1080, 1.3, False)
