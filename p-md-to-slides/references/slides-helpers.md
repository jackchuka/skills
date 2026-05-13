# Reusable Python helpers for Google Slides batchUpdate

Copy this into your per-deck `/tmp/p-md-to-slides/<deck-name>/build.py` (or `upgrade.py`) and add per-slide content beneath. The class is small enough to embed verbatim rather than imported.

## Why a copy-paste pattern

Per-deck visual treatments diverge — one deck wants giant numerals, another wants colored flow boxes. A shipped library would force a stable API; an embedded helper is throwaway and freely modifiable for the deck at hand. The helpers themselves are ~150 lines, low cost to paste.

## The helpers

```python
"""Helpers for building Google Slides batchUpdate requests.
Standard 16:9 page is 720pt × 405pt. 1pt = 12,700 EMU.
"""
import json

EMU = 12700
PAGE_W = 720
PAGE_H = 405
PAD = 35  # standard edge padding


def pt(v): return int(v * EMU)


def rgb(t):
    """Accept (r,g,b) ints 0–255, floats 0.0–1.0, or hex str like '#10122b'."""
    if isinstance(t, str):
        h = t.lstrip("#")
        t = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = t
    if max(r, g, b) > 1.0:
        return {"red": r/255.0, "green": g/255.0, "blue": b/255.0}
    return {"red": r, "green": g, "blue": b}


def blend(a, b, alpha):
    """Pre-blend (r,g,b) a over (r,g,b) b at alpha (1.0 = all a).
    Use this for 'muted' text colors — foregroundColor has no alpha field."""
    if isinstance(a, dict): a = (a["red"], a["green"], a["blue"])
    if isinstance(b, dict): b = (b["red"], b["green"], b["blue"])
    if max(a) > 1.0: a = tuple(x/255.0 for x in a)
    if max(b) > 1.0: b = tuple(x/255.0 for x in b)
    return tuple(alpha*x + (1-alpha)*y for x, y in zip(a, b))


class Slide:
    """Builds a list of batchUpdate requests. Append to .requests, dump as JSON."""

    def __init__(self):
        self.requests = []

    # ── Slides ───────────────────────────────────────────────────────
    def create_slide(self, slide_id, index, blank_layout_id, bg=None):
        self.requests.append({"createSlide": {
            "objectId": slide_id,
            "insertionIndex": index,
            "slideLayoutReference": {"layoutId": blank_layout_id},
        }})
        if bg is not None:
            self.set_background(slide_id, bg)

    def set_background(self, slide_id, color):
        self.requests.append({"updatePageProperties": {
            "objectId": slide_id,
            "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(color)}}}},
            "fields": "pageBackgroundFill.solidFill.color",
        }})

    def delete(self, object_id):
        self.requests.append({"deleteObject": {"objectId": object_id}})

    # ── Shapes ───────────────────────────────────────────────────────
    def add_textbox(self, page_id, obj_id, x, y, w, h):
        self.requests.append({"createShape": {
            "objectId": obj_id, "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {"width": {"magnitude": pt(w), "unit": "EMU"},
                          "height": {"magnitude": pt(h), "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1,
                               "translateX": pt(x), "translateY": pt(y),
                               "unit": "EMU"},
            },
        }})

    def add_rect(self, page_id, obj_id, x, y, w, h, fill_color, fill_alpha=1.0):
        self.requests.append({"createShape": {
            "objectId": obj_id, "shapeType": "RECTANGLE",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {"width": {"magnitude": pt(w), "unit": "EMU"},
                          "height": {"magnitude": pt(h), "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1,
                               "translateX": pt(x), "translateY": pt(y),
                               "unit": "EMU"},
            },
        }})
        self.requests.append({"updateShapeProperties": {
            "objectId": obj_id,
            "shapeProperties": {
                "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(fill_color)}, "alpha": fill_alpha}},
                "outline": {"propertyState": "NOT_RENDERED"},
            },
            "fields": "shapeBackgroundFill.solidFill,outline.propertyState",
        }})

    # ── Text ─────────────────────────────────────────────────────────
    def insert_text(self, obj_id, text):
        self.requests.append({"insertText": {"objectId": obj_id, "text": text}})

    def style_all(self, obj_id, font="DM Sans", size=10, weight=400, color=None):
        style = {"fontFamily": font,
                 "weightedFontFamily": {"fontFamily": font, "weight": weight},
                 "fontSize": {"magnitude": size, "unit": "PT"}}
        fields = "fontFamily,weightedFontFamily,fontSize"
        if weight >= 700:
            style["bold"] = True; fields += ",bold"
        if color is not None:
            style["foregroundColor"] = {"opaqueColor": {"rgbColor": rgb(color)}}
            fields += ",foregroundColor"
        self.requests.append({"updateTextStyle": {
            "objectId": obj_id, "textRange": {"type": "ALL"},
            "style": style, "fields": fields,
        }})

    def style_range(self, obj_id, start, end, font=None, size=None, weight=None, color=None):
        style = {}; fields = []
        if font is not None:
            style["fontFamily"] = font
            style["weightedFontFamily"] = {"fontFamily": font, "weight": weight or 400}
            fields += ["fontFamily", "weightedFontFamily"]
        if size is not None:
            style["fontSize"] = {"magnitude": size, "unit": "PT"}; fields.append("fontSize")
        if weight is not None:
            style["bold"] = (weight >= 700); fields.append("bold")
        if color is not None:
            style["foregroundColor"] = {"opaqueColor": {"rgbColor": rgb(color)}}
            fields.append("foregroundColor")
        self.requests.append({"updateTextStyle": {
            "objectId": obj_id,
            "textRange": {"type": "FIXED_RANGE", "startIndex": start, "endIndex": end},
            "style": style, "fields": ",".join(fields),
        }})

    def align(self, obj_id, alignment="START", line_spacing=115):
        self.requests.append({"updateParagraphStyle": {
            "objectId": obj_id, "textRange": {"type": "ALL"},
            "style": {"alignment": alignment, "lineSpacing": line_spacing},
            "fields": "alignment,lineSpacing",
        }})

    # ── Z-order ──────────────────────────────────────────────────────
    def send_to_back(self, obj_id):
        self.requests.append({"updatePageElementsZOrder": {
            "pageElementObjectIds": [obj_id], "operation": "SEND_TO_BACK"}})

    # ── Composite ────────────────────────────────────────────────────
    def top_bar(self, page_id, prefix, left, right, color):
        """Standard top bar. Skips an empty slot — the API rejects style ops on empty text."""
        if left:
            lid = f"{page_id}_{prefix}_tbl"
            self.add_textbox(page_id, lid, PAD, 14, 350, 16)
            self.insert_text(lid, left)
            self.style_all(lid, font="DM Sans", size=8, weight=500, color=color)
            self.align(lid, "START")
        if right:
            rid = f"{page_id}_{prefix}_tbr"
            self.add_textbox(page_id, rid, PAGE_W - PAD - 350, 14, 350, 16)
            self.insert_text(rid, right)
            self.style_all(rid, font="DM Sans", size=8, weight=500, color=color)
            self.align(rid, "END")
```

## Usage skeleton

```python
s = Slide()

# Title slide (size=40, not 36 — projection-readable default)
s.create_slide("deck_s01", 0, BLANK, bg=NAVY)
s.top_bar("deck_s01", "tb", "FINDY LT · 2026.05.13", "", MUTED_CREAM)
s.add_textbox("deck_s01", "deck_s01_h", PAD, 220, PAGE_W - 2*PAD, 110)
s.insert_text("deck_s01_h", "Agent Skills を\n社内で育てる仕組み作り")
s.style_all("deck_s01_h", font="DM Sans", size=40, weight=600, color=CREAM)
s.align("deck_s01_h", "START", line_spacing=115)
# Subtitle at 16pt (not 12pt) — readable from the back row
s.add_textbox("deck_s01", "deck_s01_sub", PAD, 340, PAGE_W - 2*PAD, 24)
s.insert_text("deck_s01_sub", "@jackchuka  /  Tailor Inc.  /  Head of Platform")
s.style_all("deck_s01_sub", font="DM Sans", size=16, weight=400, color=MUTED_CREAM)
s.align("deck_s01_sub", "START")

# Content slide — body bumped to 16-18pt w600+ for projection
s.create_slide("deck_s02", 1, BLANK, bg=CREAM)
s.top_bar("deck_s02", "tb", "02 · 自己紹介", "ABOUT ME", MUTED_NAVY)
s.add_textbox("deck_s02", "deck_s02_h", PAD, 50, PAGE_W - 2*PAD, 40)
s.insert_text("deck_s02_h", "自己紹介")
s.style_all("deck_s02_h", font="DM Sans", size=24, weight=700, color=NAVY)
s.align("deck_s02_h", "START")
# Body — default to size=16 weight=700, drop to size=15 weight=600 only when 5+ items
s.add_textbox("deck_s02", "deck_s02_body", PAD, 110, PAGE_W - 2*PAD, 250)
s.insert_text("deck_s02_body", "・jackchuka  /  Head of Platform\n・Tailor Inc.  /  Headless ERP Platform")
s.style_all("deck_s02_body", font="DM Sans", size=16, weight=700, color=NAVY)
s.align("deck_s02_body", "START", line_spacing=145)

# Delete default
s.delete(DEFAULT)

# Dump
with open("/tmp/p-md-to-slides/findy/batch.json", "w") as f:
    json.dump({"requests": s.requests}, f, ensure_ascii=False)
```

## Layout coordinates cheat sheet

Standard layout regions inside the 720×405 canvas (35pt padding):

| Region | x | y | w | h | Notes |
|--------|---|---|---|---|-------|
| Top bar (left)  | 35 | 14 | 350 | 16 | 8pt label, w500, uppercase |
| Top bar (right) | 335 | 14 | 350 | 16 | flush-right alignment |
| Heading (content slide) | 35 | 50 | 650 | 40 | 22–26pt w700 |
| Heading (title slide)   | 35 | 220 | 650 | 110 | 40pt w600 bottom-anchored |
| Body (default) | 35 | 105 | 650 | 270 | 16–18pt w600–700 (projection-readable) |
| Body (dense, 5+ items) | 35 | 105 | 650 | 270 | 13–15pt w600 |
| Diagram region (with top-right numeral) | 35 | 180–260 | 650 | 130 | leave room above for numeral collision |
| Caption (footer)  | 35 | 360 | 650 | 24  | 13–15pt w400, muted |
| Decorative numeral (top-right) | 540 | 30 | 150 | 100 | Roboto Mono 75–90pt w700, dim |
| Accent bar (left of heading)  | 35 | 50 | 4 | 35 | theme accent color |

Off-canvas threshold: anything past y≈395 is invisible to viewers.

## Composite patterns

### Decorative anchor character (top-right)

A single oversized Roboto Mono glyph in the corner, dim color, used to visually
label the slide without adding reading load. Most often a number for section
slides (`"01"` / `"02"` / `"03"`), but the same recipe works for any single
symbolic character that captures the slide's role:

- `"?"` on a question slide
- `"/"` or `"//"` on a transition / divider
- `"※"` on a caveat / disclaimer slide
- `"!"` on a warning / critical-info slide
- `"01"` … `"NN"` on ordered section slides

The pattern is the same — only the glyph changes:

```python
# Whatever symbolic anchor fits the slide:
glyph = "01"   # or "?", "/", "※", "!", …

s.add_textbox(SLIDE, "anchor", PAGE_W-180, 30, 150, 100)
s.insert_text("anchor", glyph)
s.style_all("anchor", font="Roboto Mono", size=85, weight=700,
             color=blend(text_color, bg_color, 0.18))   # very dim
s.align("anchor", "END")
```

The anchor should be the *quietest* element on the slide — readers shouldn't
"read" it, they should feel it as a label. Hence the very dim color.

### Before / After diagram

Two colored rectangles with arrow + reason badge between:

```python
# Before box (light)
s.add_rect(SLIDE, "before_box", PAD, 145, 220, 120, blend(WHITE, NAVY, 0.92))
# label + title text inside
# Arrow & accent badge in middle
s.add_line(SLIDE, "arrow", PAD+230, 200, 110, 2, MUTED)
s.add_rect(SLIDE, "reason_badge", PAD+240, 220, 90, 50, BLUE)
# After box (dark)
s.add_rect(SLIDE, "after_box", PAGE_W-PAD-220, 145, 220, 120, NAVY)
```

### 2×2 card grid

For summary / wrap-up slides:

```python
positions = [(PAD-8, 97), (PAD+322, 97), (PAD-8, 212), (PAD+322, 212)]
for i, (x, y) in enumerate(positions):
    bg_id = f"card_bg_{i}"
    s.add_rect(SLIDE, bg_id, x, y, 336, 115, LIGHT_GRAY)
    s.send_to_back(bg_id)
    # Left accent bar
    s.add_rect(SLIDE, f"card_bar_{i}", x, y, 3, 115, ACCENT)
    # Text content goes on top (created later → naturally in front)
```

### Narrative-numbered card grid (recap / wrap-up)

A stronger version of the 2×2 grid when the recap has *story structure*
(課題 → 解決 → 品質 → 未来, problem → why → how → what next, etc.). Each
card carries a mono phase number + label + content. The structure tells the
audience these aren't 4 disconnected bullets — they're a sequence.

```python
phases = [
    ("01", "課題", "社内スキル共有の\n仕組みは未確立"),
    ("02", "解決", "GitHub リポジトリで\n所有者と運用を明確化"),
    ("03", "品質", "CI でフォーマットと\nセキュリティを担保"),
    ("04", "未来", "AI Agentic CI で\n自動マージまで実現"),
]
# Positions: y=97 if the slide is recap-only (no heading region);
# y=220 if you also have a heading + subhead at the top.
positions = [(PAD-8, 97), (PAD+322, 97), (PAD-8, 230), (PAD+322, 230)]

for i, ((num, label, body), (x, y)) in enumerate(zip(phases, positions)):
    bg = f"phase_bg_{i}"
    s.add_rect(SLIDE, bg, x, y, 336, 130, LIGHT_GRAY)
    s.send_to_back(bg)
    s.add_rect(SLIDE, f"phase_bar_{i}", x, y, 3, 130, ACCENT)  # Tailor Blue
    # Number (mono, accent color, top-left)
    s.add_textbox(SLIDE, f"phase_num_{i}", x+18, y+15, 80, 28)
    s.insert_text(f"phase_num_{i}", num)
    s.style_all(f"phase_num_{i}", font="Roboto Mono", size=18, weight=700,
                 color=ACCENT)
    # Label (small mono uppercase, muted)
    s.add_textbox(SLIDE, f"phase_lbl_{i}", x+90, y+18, 200, 20)
    s.insert_text(f"phase_lbl_{i}", label)
    s.style_all(f"phase_lbl_{i}", font="Roboto Mono", size=12, weight=700,
                 color=MUTED_NAVY)
    # Body (big, bold, navy)
    s.add_textbox(SLIDE, f"phase_body_{i}", x+18, y+50, 305, 70)
    s.insert_text(f"phase_body_{i}", body)
    s.style_all(f"phase_body_{i}", font="DM Sans", size=16, weight=700,
                 color=NAVY)
    s.align(f"phase_body_{i}", "START", line_spacing=140)
```

### Dark footer band (cream summary slide closer)

When the wrap-up slide is cream and you want to physically separate the
"summary content" from the "thank you / contact" close, place a navy band
across the bottom at y=345 holding the CTA. The contrast acts as a visual
period — it tells the audience "this is the end" without saying it.

```python
# Dark footer band
s.add_rect(SLIDE, "footer_band", 0, 345, PAGE_W, 60, NAVY)
# Left: FIND ME ON label + handles
s.add_textbox(SLIDE, "footer_lbl", PAD, 358, 250, 16)
s.insert_text("footer_lbl", "FIND ME ON")
s.style_all("footer_lbl", font="Roboto Mono", size=10, weight=700, color=ACCENT)
s.add_textbox(SLIDE, "footer_handle", PAD, 376, 400, 22)
s.insert_text("footer_handle", "X / GitHub / Zenn  @jackchuka")
s.style_all("footer_handle", font="DM Sans", size=16, weight=600, color=CREAM)
# Right: thank-you line, flush-right
s.add_textbox(SLIDE, "footer_thanks", PAGE_W-PAD-350, 370, 350, 22)
s.insert_text("footer_thanks", "ご清聴ありがとうございました")
s.style_all("footer_thanks", font="DM Sans", size=15, weight=400,
             color=blend(CREAM, NAVY, 0.6))
s.align("footer_thanks", "END")
```

### Subhead (tagline) under the heading

A 12–14pt muted single-line tag at `y≈95` that names the slide's *thesis* —
why the audience should care about what follows. Effective on content slides
where the heading is the *topic* but not the *point*. Push the body region
down to ~y=125 to leave breathing room.

```python
# Heading
s.add_textbox(SLIDE, "h", PAD, 50, PAGE_W - 2*PAD, 40)
s.insert_text("h", "工夫② マークダウンでも CI を回す")
s.style_all("h", font="DM Sans", size=24, weight=700, color=text_color)
# Subhead (the WHY)
s.add_textbox(SLIDE, "sub", PAD, 95, PAGE_W - 2*PAD, 22)
s.insert_text("sub", "スキルは「単なる md」だからこそ、運用品質を CI で守る")
s.style_all("sub", font="DM Sans", size=13, weight=400, color=muted_color)
# Body starts at y≈125 (not y=105) to leave room
```

### Flow diagram

Sequential boxes with arrows + a branching split. Note the y-coordinates:
when a slide has a decorative numeral in the top-right, push the diagram down
to ~y=190 (not y=140) so it doesn't visually collide with the numeral and feels
less cramped against the heading.

```python
# Step 1 — y=190 (sits below heading + numeral, not at the top)
s.add_rect(SLIDE, "step1", PAD, 190, 130, 70, DIM_TINT, fill_alpha=0.6)
s.add_textbox(SLIDE, "step1_t", PAD, 208, 130, 40)
s.insert_text("step1_t", "PR 作成")
s.style_all("step1_t", font="DM Sans", size=18, weight=600, color=text_color)
s.align("step1_t", "CENTER")

# Arrow
s.add_textbox(SLIDE, "arr1", PAD+135, 210, 30, 30)
s.insert_text("arr1", "▶")
s.style_all("arr1", font="DM Sans", size=16, color=MUTED)

# Step 2 (highlight color)
s.add_rect(SLIDE, "step2", PAD+170, 190, 200, 70, BLUE)
s.add_textbox(SLIDE, "step2_t", PAD+170, 202, 200, 25)
s.insert_text("step2_t", "🔐  セキュリティチェック")
s.style_all("step2_t", font="DM Sans", size=16, weight=700, color=WHITE)
s.align("step2_t", "CENTER")

# Branches at right (offset above and below the main flow line at y=215)
s.add_rect(SLIDE, "branch_a", PAD+410, 155, 245, 60, blend(BLUE, NAVY, 0.7))
s.add_rect(SLIDE, "branch_b", PAD+410, 235, 245, 60, DIM_TINT, fill_alpha=0.5)
# Branch text — 16pt w700 for primary actions, 16pt w600 for secondary
```
