# ACE theory course: video sources

Sources of a narrated course built from the [theory pages](../README.md): ten parts, 149 original sample questions,
761 slides. **The MP4s are not in this repository, and neither are the audio or the frames**: this folder holds what
they are rebuilt from.

The build depends on a private slide-and-voice kit that is not published (`~/.claude/skills/slide-video-kit`, and
Kokoro for the voices), so outside the author's machine these files are useful as a script and a diagram set rather
than as a working build.

## Files
| File | Role |
|---|---|
| `src/chNN.txt` | **The single source for a part**: slides and narration together |
| `diagrams.py`, `diagrams_more.py`, `diagrams_blueprints.py` → `svg/` | All diagrams |
| `shots/` (gitignored) | Cloud Console screenshots for `= shot` slides, taken from create forms; nothing was created |
| `course.py` | compile, frames, video, merge, stats |
| `build_cached.py` | Runs the kit's video build, with a voice cache and `say.py` |
| `say.py` | Spoken-only respellings; captions keep the written form |
| `render_check.py` | Frames, plus a browser check that no slide overflows |
| `publish.py` | Writes a local YouTube kit to `publish/` (gitignored). Uploads nothing |
| `export_questions.py` | Writes every question and reason to a printable file (gitignored) |
| `video.css`, `deck.css`, `ace.css` | Slide styles |

## Commands
```bash
python3 diagrams.py                  # after editing a diagram
./course.py frames 3                 # re-render Part 3's slides, check overflow
./course.py video 3                  # rebuild Part 3; only changed sentences are re-voiced
./course.py merge                    # stream-copy into one file, chapters combined
python3 publish.py                   # YouTube kit
```

## Source format
```
#! title: Networking
#! short: Networking
## 4.1 The VPC model                 chapter marker
= table sm new | Kicker | Title      slide; types: th table cmd cards tiles list dia shot code panel q; flags: sm new r, c2 c3, panel kinds trap watch tip key note new
Col A | Col B                        body; a "> text" line is the takeaway bar (">!" red, ">~" amber)
N: spoken text                       N teacher · V remember-this (slower) · C explanation · I exam item
[pause: 0.8]
= q | Question stem?                 two slides: the question (read aloud, then silence), the answer with a reason per option
(A) option
ans A                                or "ans A, D" for choose two
why A :: reason shown on the slide
C: the spoken explanation
= shot | Kicker | Title              a Cloud Console screenshot from shots/: first line the file name,
name.png                             then an optional caption line
~ caption
```
