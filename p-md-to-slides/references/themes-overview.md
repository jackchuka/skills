# Themes overview

Three themes ship with the skill. Pick the one closest to the audience and the event tone — full design tokens live in the per-theme files.

| Theme | Aesthetic | Best for | File |
|-------|-----------|----------|------|
| `tailor`  | Editorial, three-color (navy / cream / Tailor Blue), alternating bg rhythm | Tailor-branded talks, polished LTs | `references/themes/tailor.md` |
| `minimal` | All-cream, navy text, mid-gray accents, uniform tone | Lecture decks, internal explainers | `references/themes/minimal.md` |
| `dark`    | All-navy, cream text, electric blue accents | Tech talks, demos, after-hours events | `references/themes/dark.md` |

## Adding a custom theme

Create `references/themes/<name>.md` with the same structure:

1. **Tokens** — hex colors and pre-blended muted values
2. **Fonts** — display + mono (must be available in Google Slides)
3. **Rhythm** — list of bg roles cycled per slide
4. **Typography roles** — size/weight/color per role
5. **Accent patterns** — signature visual moves
6. **Anti-patterns** — what to avoid

Refer to `tailor.md` for a complete template.

## Theme + visual polish

Themes provide the base palette. Per-deck visual polish (giant numerals, color blocks, flow diagrams) draws from theme tokens but is content-aware. The same `Slide` helper class from `references/slides-helpers.md` builds all visual elements — theme just decides which colors and fonts go in.
