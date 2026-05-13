# Tailor theme

Editorial, three-color, restrained. Bottom-anchored title slide, alternating navy/cream rhythm, Tailor Blue used sparingly as accent.

## Tokens

```
Navy        #10122b   (primary bg, text on cream)
Cream       #f7f3e4   (secondary bg, text on navy)
Tailor Blue #5353e7   (accent — bars, badges, rare hero bg)
White       #ffffff   (text on Tailor Blue)
Light Gray  #f4f4f4   (card fill on cream)
```

Pre-blended muted colors (foregroundColor has no alpha — compute manually):

```python
MUTED_NAVY  = blend(NAVY,  CREAM, 0.55)   # on cream bg
MUTED_CREAM = blend(CREAM, NAVY,  0.55)   # on navy bg
DIM_NAVY    = blend(NAVY,  CREAM, 0.18)   # decorative on cream
DIM_CREAM   = blend(CREAM, NAVY,  0.18)   # decorative on navy
```

## Fonts

- **Display**: `DM Sans` — headings, body, top-bar labels
- **Mono**: `Roboto Mono` — decorative numerals, technical labels, code

Weights used: 400 (body), 500 (top-bar labels), 600 (title/subhead), 700 (heading/bold).

`Geist` is referenced in some Tailor brand docs but **is not available in Google Slides** — use DM Sans.

## Rhythm

Alternates `navy / cream / navy / cream …`. The title slide is navy (signature). Slot a single `Tailor Blue` for a high-impact summary/wrap-up — at most 1–2 per deck.

```python
rhythm = ["navy", "cream"]
# slide i bg = rhythm[i % 2]
# title slide (i=0) → navy
# slide 1 → cream
# slide 2 → navy
# …
```

Never two same-bg slides adjacent. If you want a Tailor Blue summary slot, swap it with the slide that would have been the same-color neighbor to preserve alternation.

## Typography roles

Sizes here are **calibrated for projection**, not for thumbnail aesthetics. A deck that "looks balanced" on a laptop preview is usually too small in a room — bumping body text by 30–50% and weight by one step is the default fix.

| Role | Font | Size | Weight | Notes |
|------|------|------|--------|-------|
| Title slide headline | DM Sans | 40 | 600 | Bottom-anchored at y≈220, color = cream |
| Title slide subtitle | DM Sans | 16 | 400 | y≈340, muted cream |
| Content heading | DM Sans | 22–26 | 700 | y=50; 26 for high-impact summary slides |
| Subhead (tagline) | DM Sans | 12–14 | 400 | y≈95, muted color, single line; tells the audience *why* the slide exists |
| Body (default) | DM Sans | 16–18 | 600–700 | y=110–125 onward (offset for subhead), line_spacing 130–145 |
| Body (dense) | DM Sans | 13–15 | 600 | Only when 5+ items need to fit |
| Card content (unified) | DM Sans | 18 | 700 | Combine card heading + body into one styled block — simpler reads better at distance |
| Top-bar label | DM Sans | 8 | 500 | uppercase, muted — never above 10pt |
| Caption / footer | DM Sans | 13–15 | 400 | muted, often centered |
| Decorative numeral | Roboto Mono | 75–90 | 700 | dim color for editorial bleed |
| Mono inline (e.g. tree) | Roboto Mono | 12 | 400 | preserve formatting |
| Diagram box title | DM Sans | 20–22 | 600 | bold text inside colored rectangles |
| Diagram box label | Roboto Mono | 12–13 | 700 | small uppercase label above box title |

**Why bigger than typical web/UI design suggestions**: at a 720pt × 405pt canvas projected onto a 3–4m screen and viewed from 5–10m back, 12pt body text becomes barely legible. Audiences default to reading the slide before listening, so unreadable text means they tune you out for 5 seconds while they squint. Default heavy and big; trim only when content actually overflows.

## Accent patterns

- **Title slide**: 4pt × 60pt Tailor Blue bar above the headline at `(35, 205)`
- **Decorative anchor character**: a single oversized Roboto Mono glyph (Tailor Blue dim or grayscale dim) in the top-right corner at `(540, 30)`, sized 75–90pt. Most often a number (`"01"`/`"02"`/`"03"` for ordered section slides), but the same pattern works for `"?"` on a question slide, `"/"` on a transition, `"※"` on a caveat, etc. The anchor visually labels the slide without adding reading load.
- **Subhead under heading**: a 12–14pt muted single-line tagline at `y≈95` that names the slide's *thesis* (e.g. `"スキルは「単なる md」だからこそ、運用品質を CI で守る"`). Effective when the heading alone doesn't preempt the audience's "why am I looking at this?" Push the body region down to `y≈125` to leave breathing room.
- **Cards**: 3pt left accent bar in Tailor Blue
- **Reason badges in diagrams**: Tailor Blue fill, white 700-weight text
- **Dark footer band on cream summary slides**: an `x=0, y=345, w=720, h=60` Navy rectangle holding CTA/contact info in cream text — visually closes the deck and physically separates wrap-up content from contact info

## Anti-patterns

- Pure white background — always cream
- Centering body text — always START
- Tailor Blue as a content background for more than 1–2 slides
- Drop shadows, gradients, rounded corners (except theme cards which can be 8–12px)
- DM Sans below 18pt for headings — loses character
