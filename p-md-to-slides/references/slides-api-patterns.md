# Google Slides API patterns and gotchas

Distilled from real iteration. Read this before generating batch update JSON.

## Canvas dimensions

Standard 16:9 presentation is **720pt × 405pt** (= 9,144,000 × 5,143,500 EMU).

```
Padding (consistent):      35pt from every edge
Top bar:                   y = 14, height = 16   (8pt labels)
Heading:                   y ≈ 50, height = 32-40 (22-24pt)
Body region:               y ≈ 90-385 (≈ 295pt of usable body)
OFF-CANVAS:                anything past y ≈ 395 is invisible to viewers
```

Common mistake: assuming the slide is 540pt tall (the "old" Slides default). Modern Google Slides defaults to 405pt for 16:9. Always verify with thumbnails.

## EMU helper

`1pt = 12700 EMU`. Coordinates and sizes in the API are always EMU. Wrap in a helper:

```python
def pt(v): return v * 12700
```

## Discovering the Blank layout

After creating a new presentation, the master layout IDs are randomized. Don't hardcode `p12` — discover at runtime:

```bash
gws slides presentations get --params '{"presentationId":"PRES_ID"}' \
  | python3 -c "import json,sys; [print(l['objectId']) for l in json.load(sys.stdin).get('layouts',[]) if l.get('layoutProperties',{}).get('displayName')=='Blank']"
```

## Default slide deletion

A new presentation comes with one default slide (typically `objectId == "p"`). After creating your own slides, delete it:

```json
{"deleteObject": {"objectId": "p"}}
```

If you don't, the deck opens on the blank intro and the user has to scroll past it.

## Object ID uniqueness

Object IDs must be unique across the entire presentation — slides AND page elements share the namespace. Don't reuse an ID for shape vs slide. The skill convention is `<deck-prefix>_<slide-key>` for slides and `<slide-id>_<element>` for elements.

Re-running a create script against the same presentation will fail with "object ID X should be unique." Either delete-and-recreate, or use unique IDs each run.

## Transactional batch update

`batchUpdate` is transactional — **any single request failing rolls back the whole batch**. Implications:

- Test in chunks if you're unsure about a new request type.
- Don't assume "the failure happened at the end so most of it landed" — check.
- When iterating, write surgical updates (`replaceAllText`, `updateTextStyle` on a known objectId) instead of recreating from scratch.

## z-order is creation order

New shapes are placed on top. To put a background rectangle behind text, send it back explicitly:

```json
{"updatePageElementsZOrder": {
  "pageElementObjectIds": ["my_card_bg"],
  "operation": "SEND_TO_BACK"
}}
```

Other operations: `SEND_BACKWARD`, `BRING_FORWARD`, `BRING_TO_FRONT`.

## Speaker notes (the BODY shape)

Each slide has `slideProperties.notesPage.pageElements[]` containing a SHAPE whose `placeholder.type == "BODY"`. That shape's `objectId` is where speaker notes go.

Discover them all at once:

```bash
gws slides presentations get \
  --params '{"presentationId":"PRES_ID","fields":"slides(objectId,slideProperties.notesPage.pageElements(objectId,shape.placeholder))"}'
```

Then for each slide, find the element where `shape.placeholder.type == "BODY"` and use its `objectId` as the target for `insertText`.

**Critical gotcha:** Empty notes have `startIndex == endIndex == 0`. Issuing `deleteText` with `{"type":"ALL"}` against fresh notes returns `400: The startIndex 0 must be less than the endIndex 0`. Use `insertText` only on empty notes; reserve `deleteText` for overwriting non-empty notes.

## Color handling

`solidFill.color` accepts `{rgbColor: {red, green, blue}}` with values in `[0.0, 1.0]`. There is **no alpha on `foregroundColor`** for text — for "muted" text, pre-blend the channels against the background:

```python
def blend(a, b, alpha):
    """blend a over b at alpha (alpha=1 means all a)"""
    return {k: alpha*a[k] + (1-alpha)*b[k] for k in ("red","green","blue")}

muted_navy = blend(NAVY, CREAM, 0.55)   # ~55% navy on cream-ish background
```

For shape fills, `solidFill` does support a separate `alpha` field — useful for semi-transparent card backgrounds:

```json
"solidFill": {"color": {"rgbColor": {...}}, "alpha": 0.18}
```

## Passing JSON via gws CLI

Inline JSON via `--json '...'` is fine for small payloads. For anything substantial (every real deck), generate to a file and pass via `$(cat ...)`:

```bash
BODY=$(cat /tmp/p-md-to-slides/upgrade.json)
gws slides presentations batchUpdate \
  --params '{"presentationId":"PRES_ID"}' \
  --json "$BODY"
```

This avoids argv length limits and quoting hell.

## Surgical edits

For small fixes (typos, swapping a label, updating a number), don't rebuild — use `replaceAllText` scoped to the target page:

```json
{"replaceAllText": {
  "containsText": {"text": "OLD STRING", "matchCase": true},
  "replaceText": "NEW STRING",
  "pageObjectIds": ["my_slide_id"]
}}
```

`pageObjectIds` scoping is important — without it the replacement runs across every slide and can clobber unrelated text.

## Font rendering caveats

- **DM Sans + Japanese**: DM Sans doesn't ship full CJK glyphs. Google Slides falls back to a system Japanese font, sometimes with a slight oblique render. Acceptable for projection; verify with thumbnails.
- **Geist**: Listed in some references but **not available** in Google Slides as of writing. Use DM Sans instead.
- **Roboto Mono**: Available and renders Japanese cleanly. Good fallback for decorative numerals or technical text.

## Common style fields cheat sheet

```python
# Text style
{
  "fontFamily": "DM Sans",
  "weightedFontFamily": {"fontFamily": "DM Sans", "weight": 700},   # 100-900
  "fontSize": {"magnitude": 22, "unit": "PT"},
  "bold": True,             # set when weight >= 700
  "italic": False,
  "foregroundColor": {"opaqueColor": {"rgbColor": {...}}}
}
# Fields mask: "fontFamily,weightedFontFamily,fontSize,bold,foregroundColor"

# Paragraph style
{
  "alignment": "START" | "CENTER" | "END" | "JUSTIFIED",
  "lineSpacing": 115        # percentage (115 = 1.15x)
}
# Fields mask: "alignment,lineSpacing"

# Shape outline (often you want to suppress)
{"outline": {"propertyState": "NOT_RENDERED"}}
# Fields mask: "outline.propertyState"
```

## Thumbnail verification is non-optional

After generating slides, always fetch thumbnails and Read them. The API doesn't return errors for off-canvas content — the slide renders, the elements just aren't visible. The only way to catch:

- Text clipped by slide bottom
- Decorative elements bleeding off the right edge
- Foreground color matching background (invisible text)
- Wrong layout selection

`scripts/get_thumbnails.py` downloads all thumbnails to a directory you can then Read one by one.
