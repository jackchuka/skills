# Minimal theme

All-cream, navy text, restrained mid-gray accents. Uniform tone — best for lecture-style talks where you want the content to lead.

## Tokens

```
Cream      #f7f3e4   (every slide background)
Navy       #10122b   (text)
Mid Gray   #78909b   (accents, secondary text, dividers)
Dim Cream  #ede9da   (subtle card / panel fill)
```

Pre-blended:

```python
MUTED_NAVY = blend(NAVY, CREAM, 0.55)
DIM_NAVY   = blend(NAVY, CREAM, 0.18)
```

## Fonts

Same as Tailor — DM Sans (display/body), Roboto Mono (decorative/code). Weights 400/500/700.

## Rhythm

Uniform cream — `rhythm = ["cream"]`. No alternation. Visual rhythm comes from content (different layouts, decorative numerals, accent shapes) rather than background contrast.

## Typography roles

Same scale as Tailor:

| Role | Font | Size | Weight | Color |
|------|------|------|--------|-------|
| Title slide headline | DM Sans | 36 | 600 | navy, bottom-anchored |
| Content heading | DM Sans | 22–24 | 700 | navy |
| Body | DM Sans | 11–13 | 400 | navy |
| Top-bar label | DM Sans | 8 | 500 | muted navy, uppercase |
| Caption | DM Sans | 10 | 400 | muted navy |
| Decorative numeral | Roboto Mono | 75–90 | 700 | mid gray at low alpha |

## Accent patterns

- Mid-gray dividers (`#78909b`) for section breaks
- Decorative numerals in mid gray, not Tailor Blue
- Card backgrounds in `#ede9da` (slightly darker than cream)

## When to pick this

- Lecture notes, walkthrough decks where you don't want brand-y visual switches
- Decks where you'll be projecting in bright rooms (cream-on-projector reads well)
- Decks for audiences who'd find Tailor Blue out of place
