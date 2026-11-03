#!/usr/bin/env python3
"""ACE course builder: one source file per part (src/chNN.txt) → slides + script → frames → MP4 → merged long video.

  course.py compile [NN…]      src → build/chNN/{video-slides.html,chNN.script.md}, lint, word count
  course.py frames  [NN…]      compile, render 1080p frames, check every slide for overflow
  course.py video   [NN…] [-j3] frames, then MP4s (voice lines cached by content, so an edit re-synthesises only what changed)
  course.py merge              out/ACE-Part-*.mp4 → out/ACE-Full-Course.mp4 (stream copy, chapters combined) + publish kit
  course.py stats              words, slides, questions, estimated and real durations
Heavy output lives in ~/.cache/ace-video/ and ~/Movies/GCP-ACE-course/, outside the repository.

Source format: see README.md."""
import html, json, pathlib, re, subprocess, sys, concurrent.futures as cf

HERE = pathlib.Path(__file__).resolve().parent
SRC, SVG = HERE / "src", HERE / "svg"
BUILD = pathlib.Path.home() / ".cache/ace-video/build"
OUT = pathlib.Path.home() / "Movies/GCP-ACE-course"
KIT = pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"
PDFPY = pathlib.Path.home() / "Projects/design-room/pdf-kit/.venv/bin/python"
TTSPY = pathlib.Path.home() / ".cache/kokoro-tts/.venv/bin/python"

HEAD = """<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=af_heart@0.82 -->
<!-- labels: N=TEACHER I=EXAM_ITEM C=EXPLANATION V=REMEMBER_THIS -->
"""
SPEECH = re.compile(r"^([NVIC]): (.+)$")
BADSPOKEN = re.compile(r"[→·≥≤~&%`*_=<>\[\]{}|]|--")

def inline(s):
    codes = []
    def stash(m):
        codes.append(f"<code>{html.escape(m.group(1))}</code>"); return f"\0{len(codes)-1}\0"
    s = re.sub(r"`([^`]+)`", stash, s)
    s = html.escape(s, quote=False).replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>").replace("&lt;br&gt;", "<br>")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"==(.+?)==", r"<mark>\1</mark>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return re.sub(r"\0(\d+)\0", lambda m: codes[int(m.group(1))], s)

def plain(s):
    return re.sub(r"\*\*|==|`|(?<![\w*])\*(?=\S)|(?<=\S)\*(?![\w*])", "", s)

def cells(line):
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]

def takeaways(body):
    keep, lines = [], []
    for b in body:
        m = re.match(r"^>([!~]?) (.+)$", b)
        if m:
            lines.append(f'<div class="line{ {"!":" r","~":" a"}.get(m.group(1),"") }">{inline(m.group(2))}</div>')
        else:
            keep.append(b)
    return keep, "".join(lines)

class Chapter:
    def __init__(self, nn):
        self.nn, self.n = nn, int(nn)
        self.slides, self.script, self.lint, self.questions = [], [], [], []
        self.short, self.section, self.title = "", "", ""
        self.pending_q = None

    def head(self, flags):
        return " ".join(f for f in flags if f in ("new",))

    def slide(self, cls, inner):
        self.slides.append(f'<div class="slide {cls}">{inner}'
                           f'<div class="foot"><span>GCP ACE · Part {self.n} · {html.escape(self.short)}</span>'
                           f'<span>{html.escape(self.section)}</span></div></div>')
        self.script.append(f"\n[slide: @@{len(self.slides)}@@]")

    def top(self, k, t, red=False):
        return f'<div class="k{" r" if red else ""}">{inline(k)}</div><h1>{inline(t)}</h1>' if t else f'<div class="k{" r" if red else ""}">{inline(k)}</div>'

    def emit(self, typ, flags, fields, body):
        new = "new" if "new" in flags else ""
        red = "r" in flags
        k = fields[0] if fields else ""; t = fields[1] if len(fields) > 1 else ""
        body, lines = takeaways(body)
        if typ == "th":
            sub = f'<div class="sub">{inline(fields[2])}</div>' if len(fields) > 2 and fields[2] else ""
            self.slide(f"th {new}", f'<div class="lbl">{inline(k)}</div><div class="s">{inline(t)}</div>{sub}')
        elif typ in ("table", "cmd"):
            rows = [cells(b) for b in body]
            if len(rows) > 8: self.lint.append(f"{t!r}: {len(rows)} rows")
            head = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
            def td(c): return f"<td>{c.strip('`') and html.escape(c.strip('`'))}</td>"
            if typ == "cmd":
                tr = "".join(f"<tr><td>{inline(r[0])}</td>{td(r[1])}</tr>" for r in rows[1:])
            else:
                tr = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            cls = "bt" + (" sm" if "sm" in flags else "") + (" cmd" if typ == "cmd" else "")
            self.slide(new, self.top(k, t, red) + f'<table class="{cls}"><tr>{head}</tr>{tr}</table>{lines}')
        elif typ == "cards":
            n = next((f for f in flags if re.fullmatch(r"c\d", f)), f"c{min(len(body),4)}")
            cs = ""
            for b in body:
                m = re.match(r"^(?:(red|grn|amb) )?(.+?) :: (.+)$", b)
                if not m: sys.exit(f"bad card: {b}")
                cs += f'<div class="cd {m.group(1) or ""}"><h3>{inline(m.group(2))}</h3><p>{inline(m.group(3))}</p></div>'
            self.slide(new, self.top(k, t, red) + f'<div class="cards {n}">{cs}</div>{lines}')
        elif typ == "tiles":
            ts = "".join((lambda c: f'<div class="tile"><b>{inline(c[0])}</b><span>{inline(c[1])}</span></div>')(cells(b)) for b in body)
            self.slide(new, self.top(k, t, red) + f'<div class="tiles" style="--n:{len(body)}">{ts}</div>{lines}')
        elif typ == "list":
            lead = "".join(f'<p class="lead">{inline(b[2:])}</p>' for b in body if b.startswith("~ "))
            its = "".join(f"<li>{inline(b[2:])}</li>" for b in body if b.startswith("- "))
            self.slide(new, self.top(k, t, red) + lead + f'<ul class="big">{its}</ul>{lines}')
        elif typ == "dia":
            name = body[0].strip()
            if not (SVG / f"{name}.svg").exists(): self.lint.append(f"missing diagram {name}")
            self.slide("dia " + new, self.top(k, t, red) + f'<figure class="grow"><!--SVG:{name}--></figure>{lines}')
        elif typ == "code":
            self.slide(new, self.top(k, t, red) + f'<pre class="code">{html.escape(chr(10).join(body))}</pre>{lines}')
        elif typ == "panel":
            kind = next((f for f in flags if f in ("trap", "watch", "tip", "key", "new", "note")), "key")
            label = {"trap": "Exam trap", "watch": "Easy to confuse", "tip": "How to spot it", "key": "Remember", "new": "New in the June 2026 guide", "note": "Worth knowing"}[kind]
            ps = "".join(f"<p>{inline(b)}</p>" for b in body)
            self.slide(new, self.top(k, t, kind == "trap") + f'<div class="panel {kind}"><div class="pl">{label}</div>{ps}</div>{lines}')
        else:
            sys.exit(f"unknown slide type {typ}")

    def question(self, flags, fields, body):
        stem = fields[0]
        opts = {m.group(1): m.group(2) for m in (re.match(r"^\(([A-F])\) (.+)$", b) for b in body) if m}
        ans = next(b[4:].replace(" ", "").split(",") for b in body if b.startswith("ans "))
        why = {m.group(1): m.group(2) for m in (re.match(r"^why ([A-F]) :: (.+)$", b) for b in body) if m}
        qn = len(self.questions) + 1
        multi = len(ans) > 1
        if set(opts) - set(why): self.lint.append(f"Q{qn}: no reason for {set(opts) - set(why)}")
        if set(ans) - set(opts): self.lint.append(f"Q{qn}: answer not among options")
        kind = "Choose " + {2: "two", 3: "three"}[len(ans)] if multi else "Choose one"
        who = f"Part {self.n} · sample question {qn} · {kind}"
        ops = "".join(f'<div class="opt"><b class="l">{l}</b><span>{inline(x)}</span></div>' for l, x in opts.items())
        self.slide("qz", f'<div class="who">{who}</div><div class="stem">{inline(stem)}</div>{ops}'
                         f'<div class="hint">Pause and decide. Name the phrase in the stem that decides it.</div>')
        read = plain(stem) + " " + " ".join(f"{l}. {plain(x).rstrip('.')}." for l, x in opts.items())
        self.script.append("I: " + read)
        pause = 9 if multi else 7
        self.script.append(f"[pause: {pause}]")
        rev = "".join(f'<div class="opt {"ok" if l in ans else "no"}"><b class="l">{l}</b>{inline(x)}'
                      f'<span class="why">{"Correct. " if l in ans else ""}{inline(why.get(l, ""))}</span></div>' for l, x in opts.items())
        self.slide("qz rev", f'<div class="who">Question {qn} · answer {", ".join(ans)}</div><div class="stem">{inline(stem)}</div>{rev}')
        self.questions.append((stem, opts, ans, why))

    def parse(self, text):
        cur = None
        def flush():
            nonlocal cur
            if cur:
                (self.question(cur[1], cur[2], cur[3]) if cur[0] == "q" else self.emit(*cur))
                cur = None
        for raw in text.splitlines():
            line = raw.rstrip()
            if line.startswith("#!"):
                m = re.match(r"#!\s*(\w+):\s*(.+)", line); setattr(self, m.group(1), m.group(2)); continue
            if cur and cur[0] == "code" and not SPEECH.match(line) and not line.startswith(("= ", "## ", "[pause")):
                cur[3].append(line); continue
            if not line.strip(): continue
            if line.startswith("## "):
                flush(); self.section = line[3:]; self.script.append(f"\n{line}"); continue
            if line.startswith("= "):
                flush()
                parts = cells(line[2:]); head = parts[0].split()
                cur = [head[0], head[1:], parts[1:], []]; continue
            m = SPEECH.match(line)
            if m or line.startswith("[pause"):
                flush()
                if m:
                    if BADSPOKEN.search(m.group(2)): self.lint.append("symbol in speech: " + m.group(2)[:70])
                    if len(m.group(2).split()) > 110: self.lint.append("long line: " + m.group(2)[:50])
                self.script.append(line); continue
            if cur: cur[3].append(line.strip()); continue
            sys.exit(f"ch{self.nn}: stray line: {line[:80]}")
        flush()

    def write(self):
        d = BUILD / f"ch{self.nn}"; d.mkdir(parents=True, exist_ok=True)
        pad = len(str(len(self.slides)))
        style = f'<style>.slide::after {{ content: "{self.n}." counter(sl); }}</style>'
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>ACE</title>'
                '<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="deck.css">'
                f'<link rel="stylesheet" href="video.css"><link rel="stylesheet" href="ace.css">{style}</head><body>\n'
                + "\n".join(self.slides) + "\n</body></html>\n")
        (d / "video-slides.html").write_text(page, encoding="utf-8")
        sc = "\n".join(self.script)
        sc = re.sub(r"@@(\d+)@@", lambda m: "v-" + m.group(1).zfill(pad), sc)
        (d / f"ch{self.nn}.script.md").write_text(f"# GCP ACE Part {self.n}: {self.title}\n{HEAD}\n{sc}\n", encoding="utf-8")
        words = sum(len(s.split()) - 1 for s in self.script if SPEECH.match(s))
        return dict(nn=self.nn, title=self.title, slides=len(self.slides), words=words, q=len(self.questions))

def chapters(args):
    want = [a.zfill(2) for a in args if a.isdigit()]
    return [p.stem[2:] for p in sorted(SRC.glob("ch*.txt")) if not want or p.stem[2:] in want]

def compile_ch(nn):
    c = Chapter(nn); c.parse((SRC / f"ch{nn}.txt").read_text(encoding="utf-8"))
    info = c.write()
    for l in c.lint: print(f"  ch{nn} lint: {l}")
    pauses = sum(float(x) for x in re.findall(r"\[pause: ([\d.]+)\]", "\n".join(c.script)))
    info["est_min"] = round((info["words"] * 0.43 + pauses * 0.6) / 60, 1)
    print(f"ch{nn}: {info['slides']} slides, {info['words']} words, {info['q']} questions, ~{info['est_min']} min — {info['title']}")
    return c, info

def frames_ch(nn):
    d = BUILD / f"ch{nn}"; f = d / "frames"
    if f.exists():
        for p in f.glob("*.png"): p.unlink()
    subprocess.run([str(PDFPY), str(HERE / "render_check.py"), str(d / "video-slides.html"), str(HERE), str(f)], check=True)

def video_ch(nn):
    d = BUILD / f"ch{nn}"; OUT.mkdir(parents=True, exist_ok=True)
    c = Chapter(nn); c.parse((SRC / f"ch{nn}.txt").read_text(encoding="utf-8"))
    slug = re.sub(r"[^A-Za-z0-9]+", "-", c.title).strip("-")
    out = OUT / f"ACE-Part-{nn}-{slug}.mp4"
    log = d / "build.log"
    with log.open("w") as lf:
        subprocess.run([str(TTSPY), str(HERE / "build_cached.py"), str(d / f"ch{nn}.script.md"), "--frames", str(d / "frames"), "--out", str(out)],
                       check=True, stdout=lf, stderr=subprocess.STDOUT)
    print(log.read_text().splitlines()[-1] if False else f"built {out.name}", flush=True)

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_chapters", "-show_streams", "-show_format", "-of", "json", str(p)], check=True, capture_output=True, text=True)
    return json.loads(r.stdout)

def clock(s):
    s = int(s); h, m, s = s // 3600, s // 60 % 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def merge():
    parts = sorted(OUT.glob("ACE-Part-*.mp4"))
    if not parts: sys.exit("no parts")
    sig = None; meta = [";FFMETADATA1", "title=Google Cloud Associate Cloud Engineer: the full course (June 2026 exam guide)"]; t = 0.0; rows = []
    lst = OUT / ".concat.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    for p in parts:
        d = probe(p)
        s = tuple((x["codec_type"], x["codec_name"], x.get("width"), x.get("height"), x.get("r_frame_rate"), x.get("sample_rate"), x.get("channels"), x.get("pix_fmt"), x.get("profile"))
                  for x in d["streams"] if x["codec_type"] in ("video", "audio"))
        if sig and s != sig: sys.exit(f"{p.name}: stream parameters differ, cannot stream-copy: {s} vs {sig}")
        sig = s
        for c in d["chapters"]:
            a, b = float(c["start_time"]) + t, float(c["end_time"]) + t
            meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(a*1000)}", f"END={int(b*1000)}", "title=" + c["tags"]["title"]]
            rows.append((a, c["tags"]["title"]))
        t += float(d["format"]["duration"])
    mf = OUT / ".chapters.txt"; mf.write_text("\n".join(meta) + "\n", encoding="utf-8")
    out = OUT / "ACE-Full-Course.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(mf), "-map", "0", "-map_metadata", "1", "-map_chapters", "1",
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    (OUT / "chapters.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    real = float(probe(out)["format"]["duration"])
    print(f"{out}: {clock(real)} (sum of parts {clock(t)}), {len(rows)} chapters, {out.stat().st_size/1e9:.2f} GB")

def main():
    cmd = sys.argv[1]; args = sys.argv[2:]
    jobs = next((int(a[2:]) for a in args if a.startswith("-j")), 3)
    nns = chapters(args)
    if cmd in ("compile", "frames", "video", "stats"):
        infos = [compile_ch(n)[1] for n in nns]
        if len(infos) > 1:
            print(f"TOTAL {sum(i['slides'] for i in infos)} slides, {sum(i['words'] for i in infos)} words, {sum(i['q'] for i in infos)} questions, ~{sum(i['est_min'] for i in infos)/60:.1f} h")
    if cmd in ("frames", "video"):
        with cf.ThreadPoolExecutor(4) as ex: list(ex.map(frames_ch, nns))
    if cmd == "video":
        with cf.ThreadPoolExecutor(jobs) as ex: list(ex.map(video_ch, nns))
    if cmd == "merge":
        merge()
    if cmd == "stats":
        for p in sorted(OUT.glob("*.mp4")):
            d = probe(p); print(f"{p.name}: {clock(float(d['format']['duration']))}, {len(d['chapters'])} chapters, {p.stat().st_size/1e6:.0f} MB")

if __name__ == "__main__":
    main()
