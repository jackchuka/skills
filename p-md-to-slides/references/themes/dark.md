# Dark theme

All-navy, cream text, electric blue accents. After-hours / demo-mode aesthetic — best for tech talks where the audience expects a dark deck.

## Tokens

```
Deep Navy      #0b0d20   (every slide background — slightly deeper than Tailor)
Cream          #f7f3e4   (text)
Electric Blue  #5353e7   (accent — headings, links, hero cards)
White          #ffffff   (text on Electric Blue surfaces)
Soft Panel     #1a1d35   (card / panel fill on dark bg)
```

Pre-blended:

```python
MUTED_CREAM = blend(CREAM, DEEP_NAVY, 0.55)
DIM_CREAM   = blend(CREAM, DEEP_NAVY, 0.18)
```

## Fonts

Same as Tailor — DM Sans (display/body), Roboto Mono (decorative/code).

## Rhythm

Uniform deep navy — `rhythm = ["deep_navy"]`. For a hero / summary slot, swap to Electric Blue (`#5353e7`) as the background for 1 slide. Don't use Electric Blue as a frequent surface; it's overwhelming at presentation scale.

## Typography roles

Same scale as Tailor, with cream text:

| Role | Font | Size | Weight | Color |
|------|------|------|--------|-------|
| Title slide headline | DM Sans | 36 | 600 | cream, bottom-anchored |
| Content heading | DM Sans | 22–24 | 700 | cream |
| Body | DM Sans | 11–13 | 400 | cream |
| Top-bar label | DM Sans | 8 | 500 | muted cream, uppercase |
| Caption | DM Sans | 10 | 400 | muted cream |
| Decorative numeral | Roboto Mono | 75–90 | 700 | Electric Blue at low alpha (`blend(BLUE, NAVY, 0.35)`) |

## Accent patterns

- Electric Blue underlines on key phrases (Tailor-style accent bar)
- Decorative numerals in dim Electric Blue (not cream — keeps them subordinate)
- Card backgrounds in `#1a1d35` with 1pt Electric Blue left border

## When to pick this

- Tech talks, demos, anywhere "dark mode" is the expected aesthetic
- DJ-set / after-party adjacent events
- Decks heavy with code blocks — dark bg + Roboto Mono lines feel native

## Anti-patterns

- Don't use Tailor Blue as a fill on more than 1–2 slides (eye fatigue)
- Cream-on-navy at body weight (400) below 11pt — illegibility on projection
- Pure black bg — always slightly desaturated navy for warmth
