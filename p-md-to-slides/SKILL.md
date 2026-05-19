---
name: p-md-to-slides
license: MIT
description: Convert a structured Markdown deck source into a styled Google Slides presentation. Use this skill when the user has a slide.md file (or wants to write one) and wants Google Slides output — talks, LT decks, lecture slides, conference presentations, internal explainers. Trigger phrases include "md からスライド作って", "slide.md を Google Slides にして", "発表資料を Google Slides で", "convert this markdown to slides", "build a Google Slides deck from this markdown", "make slides from md", "/md-to-slides", and similar. Also use when the user references a presentation/<date>/slide.md file structure with `## Slide N — title`, `**話すこと:**`, and `**スライド要素:**` sections.
metadata:
  author: jackchuka
  scope: personal
---

# p-md-to-slides

Convert a Markdown deck source into a styled Google Slides presentation, with a chosen design theme and speaker notes pushed from the source.

## When to use

- The user has a `slide.md` (or similar) with `## Slide N — title` sections and wants Google Slides
- The user is preparing a talk / LT / conference presentation and has drafted the content in Markdown
- The user asks to convert / build / generate slides from a Markdown source

Not for activity-driven decks (see `o-tailor-allhands-deck` for those) — this is for hand-authored Markdown → Google Slides.

## Prerequisites

- `gws` CLI installed and authenticated (`gws auth login` if needed)
- Python 3 on PATH (for one-shot heredoc snippets)
- Network access to Google Slides API

## Input format

See `references/md-format.md` for the full spec. Quick summary:

```markdown
# <deck title>

## Slide N — <subtitle>

**話すこと:**
<speaker notes — pushed to the slide's notes BODY>

**スライド要素:**
- <visual element hint 1>
- <visual element hint 2>
```

Both `**話すこと:**` and `**スライド要素:**` are optional per slide.

## Workflow

The skill is intentionally lightweight — no shipped scripts. Every step is a concrete shell or Python heredoc that Claude executes inline, with patterns referenced from `references/`.

### Step 1: Read the source

Use the Read tool on the user's `slide.md`. Confirm:
- The file exists and parses (look for at least one `## Slide N —` line)
- The slide count matches what the user expects
- Identify which slides have `**話すこと:**` and which don't

If the user is starting from scratch, offer to scaffold a `slide.md` from a brief.

### Step 2: Pick a theme

Read the relevant theme reference file based on user preference (default `tailor` if not specified):

- `references/themes/tailor.md` — Tailor brand (navy/cream/blue, DM Sans + Roboto Mono, alternating rhythm)
- `references/themes/minimal.md` — All-cream, navy text
- `references/themes/dark.md` — All-navy, cream text, electric blue accents

If the user wants something custom, ask for brand colors + display font and adapt inline.

### Step 3: Parse the markdown

A short Python heredoc handles the parsing. The format is small enough that this beats a separate script.

```bash
python3 - <<'PY' > /tmp/p-md-to-slides/parsed.json
import json, re, sys
from pathlib import Path

SRC = "/path/to/slide.md"  # ← fill in
SLIDE_HEADER = re.compile(r"^##\s*Slide\s*(\d+)\s*[—–-]\s*(.+?)\s*$")
BLOCK_MARKER = re.compile(r"^\*\*([^*]+):\*\*\s*$")
BULLET = re.compile(r"^\s*[-*]\s+(.*)$")

text = Path(SRC).read_text(encoding="utf-8")
lines = text.splitlines()

title = next((l[2:].strip() for l in lines if l.startswith("# ") and not l.startswith("## ")), "")
starts = [i for i, l in enumerate(lines) if SLIDE_HEADER.match(l)]
slides = []
for idx, start in enumerate(starts):
    end = starts[idx+1] if idx+1 < len(starts) else len(lines)
    m = SLIDE_HEADER.match(lines[start])
    blocks = {}
    code_blocks = []
    current = None
    in_code = False
    code_buf = []
    for line in lines[start+1:end]:
        if line.lstrip().startswith("```"):
            if in_code:
                code_blocks.append("\n".join(code_buf)); code_buf = []; in_code = False
            else:
                current = None; in_code = True
            continue
        if in_code: code_buf.append(line); continue
        mm = BLOCK_MARKER.match(line)
        if mm:
            current = mm.group(1).strip()
            blocks.setdefault(current, []); continue
        if line.strip() == "---":
            current = None; continue
        if current is not None:
            blocks[current].append(line)
    notes = "\n".join(blocks.get("話すこと", [])).strip()
    elements_raw = "\n".join(blocks.get("スライド要素", [])).strip()
    elements = [BULLET.match(l).group(1).strip() for l in elements_raw.splitlines() if BULLET.match(l)]
    slides.append({"index": idx, "number": int(m.group(1)), "subtitle": m.group(2).strip(),
                    "notes": notes, "elements": elements, "elements_raw": elements_raw,
                    "code_blocks": code_blocks})
print(json.dumps({"title": title, "slides": slides}, ensure_ascii=False, indent=2))
PY
```

Inspect the JSON briefly (slide count, notes lengths) before continuing.

### Step 4: Create the presentation shell

```bash
gws slides presentations create --json '{"title":"<deck title>"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('PRES_ID=' + d['presentationId']); print('BLANK=' + next(l['objectId'] for l in d.get('layouts',[]) if l.get('layoutProperties',{}).get('displayName')=='Blank')); print('DEFAULT=' + d['slides'][0]['objectId'])"
```

Capture `PRES_ID`, `BLANK` (Blank layout ID), and `DEFAULT` (default slide ID — must delete later).

### Step 5: Build the deck

Write a one-off `/tmp/p-md-to-slides/<deck-name>/build.py` that emits batchUpdate JSON. Read `references/slides-helpers.md` for the helper code pattern (page constants, color blending, `Slide` builder class) — copy the helpers into your build script, then add per-slide content.

The base recipe per slide:
1. `create_slide(slide_id, index, BLANK, bg=theme_bg_for_index)` — bg cycles per theme `rhythm`
2. `top_bar(...)` — small uppercase labels (e.g. `"05 · 工夫① ..."`)
3. Heading — `22–24pt w700` for content slides, `40pt w600` bottom-anchored for the title slide
4. Body — `16–18pt w600–700` bullets from `elements`, or fall back to a clean prose dump

**Projection-readable defaults.** Sizes are calibrated for talks projected on a 3–4m screen viewed from 5–10m back. A deck that "looks balanced" in your laptop preview is usually too small in the room. Default heavy and big; trim only when content actually overflows. See the typography table in the chosen theme file for the full role-by-role scale.

At the end, `delete(DEFAULT)` to remove the auto-created blank slide, then push the batch:

```bash
BODY=$(cat /tmp/p-md-to-slides/<deck-name>/batch.json)
gws slides presentations batchUpdate \
  --params '{"presentationId":"<PRES_ID>"}' \
  --json "$BODY"
```

batchUpdate is transactional — if anything fails, nothing applies. Inspect the error response carefully.

### Step 6: Push speaker notes

Discover the notes BODY shape per slide, then `insertText`:

```bash
gws slides presentations get \
  --params '{"presentationId":"<PRES_ID>","fields":"slides(objectId,slideProperties.notesPage.pageElements(objectId,shape.placeholder))"}' \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
for s in d['slides']:
    sid = s['objectId']
    for el in s.get('slideProperties', {}).get('notesPage', {}).get('pageElements', []):
        if el.get('shape', {}).get('placeholder', {}).get('type') == 'BODY':
            print(f'{sid}|{el[\"objectId\"]}')
"
```

For each slide, build an `insertText` request against the notes BODY objectId with the slide's `notes` text. Skip slides without notes. **Don't use `deleteText` on empty notes** — see gotcha in `references/slides-api-patterns.md`.

### Step 7: Verify with thumbnails

```bash
mkdir -p /tmp/p-md-to-slides/<deck-name>/thumbs
gws slides presentations get --params '{"presentationId":"<PRES_ID>","fields":"slides.objectId"}' \
  | python3 -c "import json,sys; [print(s['objectId']) for s in json.load(sys.stdin)['slides']]" \
  | nl | while read i sid; do
    url=$(gws slides presentations pages getThumbnail \
      --params "{\"presentationId\":\"<PRES_ID>\",\"pageObjectId\":\"$sid\",\"thumbnailProperties.mimeType\":\"PNG\",\"thumbnailProperties.thumbnailSize\":\"LARGE\"}" \
      | python3 -c "import json,sys;print(json.load(sys.stdin)['contentUrl'])")
    curl -s -o "/tmp/p-md-to-slides/<deck-name>/thumbs/$(printf %02d $i)_${sid}.png" "$url"
  done
```

Then Read each PNG to inspect. The slide is **only 405pt tall** — content past y≈395 is invisible. The thumbnail is the only catch.

### Step 8: Iterate on visual polish

The base deck has heading + body only. Editorial polish is content-aware and applied as a per-deck `upgrade.py`. Common moves (all using the same `Slide` builder pattern from `references/slides-helpers.md`):

- **Decorative anchor character (top-right)**: a single oversized Roboto Mono glyph in dim color. Numbers (`"01"` / `"02"` / `"03"`) for ordered section slides, but also `"?"` on question slides, `"/"` on transitions, `"※"` on caveats. The anchor labels the slide without adding reading load.
- **Subhead (tagline) under heading**: 12–14pt muted single line at `y≈95`. Names the slide's *thesis* — the "why am I looking at this?" — not just the topic. Particularly effective on section / content slides where the heading alone is the topic name.
- **"Before / After" or "Journey" slides**: colored rectangles with arrow between, accent badge for the "why"
- **Flow diagrams**: colored boxes per stage, contrasting fills for branches
- **Title slide**: small accent bar (theme `accent`) above the headline
- **Summary slides (simple)**: 2×2 cards with light fill and left accent bar
- **Summary slides (story-structured)**: narrative-numbered cards (`01 課題 / 02 解決 / 03 品質 / 04 未来`). Use when the recap has a sequence, not just 4 independent points — the numbers tell the audience this is a story arc.
- **Dark footer band (cream summary closer)**: navy band at the bottom of a cream summary slide holding CTA / contact info. Acts as a visual period — physically separates "what we covered" from "thank you / find me here."

Apply by writing a fresh batchUpdate, re-fetch thumbnails, iterate.

### Step 9: Deliver

```
https://docs.google.com/presentation/d/<PRES_ID>/edit
```

## Key gotchas (full list: `references/slides-api-patterns.md`)

- **Page height is 405pt** — not 540. Anything past y≈395 is off-canvas.
- **Object IDs must be unique** across the entire presentation. Don't reuse.
- **Empty notes**: `startIndex==endIndex==0`; use `insertText` only, never `deleteText`.
- **batchUpdate is transactional**: one failure rolls back the whole batch.
- **z-order is creation order**: backgrounds must be `SEND_TO_BACK` explicitly.
- **DM Sans + Japanese**: falls back, may render slightly oblique. Acceptable; verify with thumbnails.

## Reference files

- `references/md-format.md` — input format spec
- `references/slides-api-patterns.md` — gotchas, color math, request shapes
- `references/slides-helpers.md` — reusable Python helper class (copy into `build.py`)
- `references/themes/{tailor,minimal,dark}.md` — design tokens per theme
