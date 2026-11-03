#!/usr/bin/env python3
"""check-gcloud.py --- verify every `gcloud [alpha|beta] GROUP ... VERB` in a markdown file against the
command surface of the locally installed Google Cloud SDK (lib/surface), i.e. that the command exists on the
release track the text uses. `beta projects move` passes; `monitoring channels create` without `beta` fails.

    ./check-gcloud.py ACE-Theory-Recap.md      exit 0 = all tracks right, 1 = findings, 2 = no SDK found

Flags are not checked here (GA flags can be checked with `gcloud CMD --help`); this is the track gate.
"""
import os, re, shutil, subprocess, sys

def sdk_surface():
    g = shutil.which("gcloud")
    if not g:
        return None
    try:
        root = subprocess.run([g, "info", "--format=value(installation.sdk_root)"],
                              capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return None
    p = os.path.join(root, "lib", "surface")
    return p if os.path.isdir(p) else None

def tracks_of(path):
    """Release tracks declared for a command file or group directory; None if it does not exist."""
    files = [path + ext for ext in (".py", ".yaml") if os.path.exists(path + ext)]
    if files:   # a command may have both: e.g. a GA .yaml beside an ALPHA/BETA .py
        text = "\n".join(open(f).read() for f in files)
    else:
        if not os.path.isdir(path):
            return None
        init = os.path.join(path, "__init__.py")
        text = open(init).read() if os.path.exists(init) else ""
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
    found = set()
    for m in re.finditer(r"ReleaseTracks\(([^)]*)\)", text):
        found |= set(re.findall(r"ReleaseTrack\.(\w+)", m.group(1)))
    for m in re.finditer(r"release_tracks:\s*\[([^\]]*)\]", text):
        found |= {x.strip() for x in m.group(1).split(",")}
    return found or {"GA", "BETA", "ALPHA"}

def main(md):
    surface = sdk_surface()
    if not surface:
        print("  gcloud SDK not found --- track check skipped"); return 2
    bad = {}
    in_code = False
    for n, line in enumerate(open(md), 1):
        for m in re.finditer(r"\bgcloud((?:\s+[a-z][a-z0-9-]*)+)", line):
            words = m.group(1).split()
            track = "GA"
            if words and words[0] in ("alpha", "beta"):
                track, words = words[0].upper(), words[1:]
            path, depth = surface, 0
            for w in words:
                p = os.path.join(path, w.replace("-", "_"))
                if os.path.isdir(p) or os.path.exists(p + ".py") or os.path.exists(p + ".yaml"):
                    path, depth = p, depth + 1
                    if not os.path.isdir(p):
                        break
                else:
                    break
            if depth == 0:
                continue
            p, ok = surface, True
            for w in words[:depth]:
                p = os.path.join(p, w.replace("-", "_"))
                t = tracks_of(p)
                if t is not None and track not in t:
                    ok = False
                    need = sorted(t)
            if not ok:
                key = ("gcloud " + ("" if track == "GA" else track.lower() + " ") + " ".join(words[:depth]))
                bad.setdefault((key, ", ".join(need)), []).append(n)
    for (cmd, need), lines in sorted(bad.items()):
        print(f"  {cmd}: not on this track (available: {need}) --- lines {lines[:6]}")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "ACE-Theory-Recap.md"))
