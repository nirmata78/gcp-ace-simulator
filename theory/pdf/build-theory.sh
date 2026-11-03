#!/usr/bin/env bash
# build-theory.sh --- QA gate + build for ACE-Theory-Recap.md
#
#   ./build-theory.sh           gate, then build ACE-Theory-Recap.pdf
#   ./build-theory.sh --check   gate only, no compile
#
# The compile goes through a .tex file and xelatex directly (not pandoc -o pdf)
# so the LaTeX log can be read: missing glyphs and overfull boxes are counted
# from the log, which is the only trustworthy signal for either.
set -euo pipefail
cd "$(dirname "$0")"
./assemble.py   # the pages in ../ are the source; ACE-Theory-Recap.md is generated from them

SRC=${SRC:-ACE-Theory-Recap.md}
OUT=${OUT:-ACE-Theory-Recap.pdf}
BUILD=.build
MIN_PAGES=30
MAX_CODE_COLS=150
fail=0
say()  { printf '  %-44s %s\n' "$1" "$2"; }
bad()  { say "$1" "FAIL  $2"; fail=1; }

echo "QA gate --- $SRC"

# 1. Fences. An unclosed ``` or ::: swallows the rest of the document and still builds.
ticks=$(grep -c '^```' "$SRC" || true)
(( ticks % 2 == 0 )) && say "code fences balanced" "ok ($((ticks/2)))" || bad "code fences balanced" "$ticks markers (odd)"
opens=$(grep -cE '^:::+ *\{' "$SRC" || true)
closes=$(grep -cE '^:::+ *$' "$SRC" || true)
[[ $opens == "$closes" ]] && say "panel fences balanced" "ok ($opens)" || bad "panel fences balanced" "$opens open vs $closes close"

# 2. Panel kinds. An unknown class renders as bare text, silently.
unknown=$(grep -oE '^:::+ *\{\.[a-z]+' "$SRC" | sed -E 's/.*\{\.//' | sort -u \
  | grep -vxE 'key|trap|tip|watch|note|new|objectives|wide|cmds' || true)
[[ -z $unknown ]] && say "panel kinds known" "ok" || bad "panel kinds known" "unknown: $(echo $unknown)"

# 3. Code width. Verbatim never wraps; a long line runs off the panel.
wide=$(awk -v max=$MAX_CODE_COLS '/^```/{f=!f;next} f && length($0)>max {print NR": "length($0)}' "$SRC")
[[ -z $wide ]] && say "code lines <= $MAX_CODE_COLS cols" "ok" || bad "code lines <= $MAX_CODE_COLS cols" "$(echo $wide | head -c 200)"

# 4. Cross-references. Every §N.M must name a real `## N.M` heading.
missing=""
for ref in $(grep -oE '§[0-9A-Z]+\.[0-9]+' "$SRC" | sort -u | sed 's/§//'); do
  grep -qE "^## ${ref//./\\.} " "$SRC" || missing+="$ref "
done
[[ -z $missing ]] && say "§ cross-references resolve" "ok" || bad "§ cross-references resolve" "no heading for: $missing"

# 5. Scope. This booklet teaches the exam, not one attempt at it .
leak=$(grep -niE 'your (q[0-9]+|miss|misses|guess)|mock exam [ab]|exam a\b|\bR[1-8] ---' "$SRC" | head -5 || true)
[[ -z $leak ]] && say "no attempt-specific language" "ok" || bad "no attempt-specific language" "$leak"

# 6. Highlights. An odd number of == on a line leaves a highlight open, which markdown then prints literally.
oddhl=$(awk '/^```/{f=!f;next} f{next} {gsub(/`[^`]*`/,""); para=para $0 " "; if (start=="") start=NR}
  /^[[:space:]]*$/ {n=gsub(/==/,"&",para); if (n%2) print start; para=""; start=""}' "$SRC" | head -5 | tr '\n' ' ')
nhl=$(awk '/^```/{f=!f;next} !f' "$SRC" | sed 's/`[^`]*`//g' | grep -o '==' | wc -l | awk '{print $1/2}')
[[ -z $oddhl ]] && say "==highlights== balanced" "ok ($nhl)" || bad "==highlights== balanced" "paragraphs at lines: $oddhl"

# 7. gcloud release tracks, against the locally installed SDK (skipped if there is none).
if trk=$(./check-gcloud.py "$SRC"); then say "gcloud commands on the right track" "ok"
elif [[ $? == 2 ]]; then say "gcloud commands on the right track" "skipped (no SDK)"
else bad "gcloud commands on the right track" "$(echo "$trk" | head -3)"; fi

# 8. Scope, second rule : theory only. Practice scenarios and their
#    answers live in ACE-Practice-Scenarios.md until they get a booklet of their own.
story=$(grep -nE '^:::+ *\{\.(story|item|answer)' "$SRC" | head -3 | tr '\n' ' ' || true)
[[ -z $story ]] && say "no practice scenarios in the theory" "ok" || bad "no practice scenarios in the theory" "$story"

# Tables inside panels are caught by the Lua filter at compile time (hard error).

[[ $fail == 0 ]] || { echo "QA gate FAILED"; exit 1; }
[[ ${1:-} == --check ]] && { echo "QA gate passed (--check: no compile)"; exit 0; }

echo "Build"
mkdir -p "$BUILD"
compile() {
  ACE_TIGHT="$tight" pandoc "$SRC" -f markdown+mark -s -o "$BUILD/recap.tex" \
    --syntax-highlighting=none \
    -H ace-theory-preamble.tex -B ace-theory-titlepage.tex \
    --lua-filter=ace-theory.lua
  ( cd "$BUILD"
    for pass in 1 2 3; do
      xelatex -interaction=nonstopmode -halt-on-error recap.tex >/dev/null 2>&1 || {
        echo "  xelatex failed on pass $pass --- last errors:"; grep -A3 '^!' recap.log | head -30; exit 1; }
    done )
}
# A part whose last page would hold only a few lines (before its recall card or the next part) is rebuilt in
# the tighter rhythm (\acetight), which usually pulls those lines back. Up to two extra rounds.
tight=""
compile
for round in 1 2; do
  short=$(./check-pages.py --tails "$BUILD/recap.pdf")
  new=$(echo "$short" | tr ',' '\n' | grep -v '^$' | grep -vxF -f <(echo "$tight" | tr ',' '\n' | grep -v '^$') || true)
  [[ -z $new ]] && break
  tight=$(echo "$tight,$(echo "$new" | paste -sd, -)" | sed 's/^,//')
  compile
done
short=$(./check-pages.py --tails "$BUILD/recap.pdf")

missing_chars=$(grep -c 'Missing character' "$BUILD/recap.log" || true)
overfull=$(grep -c '^Overfull \\hbox' "$BUILD/recap.log" || true)
bigover=$(grep -oE '^Overfull \\hbox \(([0-9.]+)pt' "$BUILD/recap.log" | grep -oE '[0-9.]+' \
  | awk '$1>6' | wc -l | tr -d ' ' || true)   # no overfull box at all is the good case: keep pipefail quiet
cp "$BUILD/recap.pdf" "$OUT"
pages=$(pdfinfo "$OUT" | awk '/^Pages:/{print $2}')

[[ $missing_chars == 0 ]] && say "missing glyphs" "ok (0)" || bad "missing glyphs" "$missing_chars --- grep 'Missing character' $BUILD/recap.log"
[[ $bigover == 0 ]] && say "overfull boxes > 6pt" "ok ($overfull small)" || bad "overfull boxes > 6pt" "$bigover (of $overfull) --- see $BUILD/recap.log"
(( pages >= MIN_PAGES )) && say "page count" "ok ($pages)" || bad "page count" "$pages < $MIN_PAGES --- aborted export?"

# 9. Page model, read back from the PDF: every part opens a page, and every recall card starts a page and
#    fits on it (the next part, or the appendix, begins on the very next page).
recall=$(./check-pages.py "$OUT" || true)
[[ $recall == ok* ]] && say "parts open pages; recall cards fit one" "$recall" || bad "parts open pages; recall cards fit one" "$recall"
[[ -z $short ]] && say "no near-empty last pages" "ok${tight:+ (tightened: $tight)}" \
  || say "no near-empty last pages" "WARN  still short after tightening: $short --- trim that part"

[[ $fail == 0 ]] && echo "Built $OUT --- $pages pages" || { echo "Build finished WITH FAILURES"; exit 1; }
