#!/usr/bin/env python3
"""HTML → 1080p PNG frames via the kit's render_slides, then an overflow check of every slide in the browser."""
import pathlib, sys
html_path, css_dir, out = map(pathlib.Path, sys.argv[1:4])
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
sys.path.insert(0, str(pathlib.Path.home() / "Projects/design-room/pdf-kit"))
import render_slides as rs
from build import inline_svgs, inline_css
from playwright.sync_api import sync_playwright
out.mkdir(parents=True, exist_ok=True)
page = inline_css(inline_svgs(html_path.read_text(encoding="utf-8"), css_dir / "svg"), css_dir)
built = html_path.with_suffix(".built.html"); built.write_text(page, encoding="utf-8")
JS = """() => [...document.querySelectorAll('.slide')].flatMap((s, i) => {
  const r = s.getBoundingClientRect(), bad = [];
  const foot = s.querySelector('.foot'); const limit = foot ? foot.getBoundingClientRect().top : r.bottom;
  if (s.scrollHeight > s.clientHeight + 2) bad.push('scrollHeight ' + (s.scrollHeight - s.clientHeight));
  if (s.scrollWidth > s.clientWidth + 2) bad.push('scrollWidth ' + (s.scrollWidth - s.clientWidth));
  for (const el of s.children) { if (el === foot) continue; const b = el.getBoundingClientRect();
    if (b.bottom > limit + 1) bad.push(el.tagName + '.' + el.className + ' past foot by ' + Math.round(b.bottom - limit));
    if (b.right > r.right - 10) bad.push(el.tagName + ' past right ' + Math.round(b.right - r.right)); }
  for (const el of s.querySelectorAll('pre,td,.opt')) { if (el.scrollWidth > el.clientWidth + 3) bad.push(el.tagName + ' clipped: ' + el.textContent.slice(0, 40)); }
  return bad.length ? [(i + 1) + ': ' + bad.join('; ')] : [];
})"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 720})
    pg.emulate_media(media="print"); pg.goto(built.as_uri(), wait_until="load"); pg.evaluate("document.fonts.ready.then(() => true)")
    issues = pg.evaluate(JS)
    pdf = html_path.with_suffix(".pdf"); pg.pdf(path=str(pdf), print_background=True, prefer_css_page_size=True); b.close()
built.unlink(); rs.from_pdf(pdf, "v", out)
print(f"{html_path.parent.name}: {len(list(out.glob('*.png')))} frames, {len(issues)} overflow issues")
for i in issues: print("  slide", i)
