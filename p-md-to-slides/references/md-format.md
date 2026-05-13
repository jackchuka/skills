# Markdown Deck Source Format

The skill expects input markdown to follow this fixed structure. Strict parsing means the deck output is predictable.

## Top-level structure

```markdown
# <deck title>                         ← H1, used as fallback presentation title

**<subtitle / event / date>**          ← optional, ignored by parser
<author / affiliation>                 ← optional, ignored by parser

---                                    ← horizontal rule between sections (optional)

## Slide 1 — タイトル                  ← H2 + em dash + slide subtitle
…

## Slide 2 — <subtitle>
…
```

## Per-slide block

Each slide starts with `## Slide <N> — <subtitle>` and contains:

```markdown
## Slide 3 — 質問

**話すこと:**
さっそくですが、質問です。みなさんの会社では…
（複数段落 OK）

**スライド要素:**
- 質問テキスト
- ハッシュタグ: `#Skillsお悩み_findy`
```

### Rules

- The H2 line *must* match `## Slide <N> — <subtitle>` (em dash `—`, not a hyphen `-`). The parser uses this as a slide boundary.
- The slide number `N` is informational — the parser uses position, not the number, for ordering. Numbers should be sequential for readability.
- `**話すこと:**` block (speaker notes): everything until the next `**…**` block or next `## Slide …` heading.
- `**スライド要素:**` block (slide elements): bullet list or free text. Used as design hints — Claude reads it to know what visuals are expected.
- Both `**話すこと:**` and `**スライド要素:**` are **optional** per slide. Title slides typically have neither, or just `**スライド要素:**`.
- Anything outside known blocks is captured into the slide's `raw_body` field for downstream use.

## Example: minimal title slide

```markdown
## Slide 1 — タイトル

**スライド要素:**

- タイトル
- 名前
- 会社ロゴ
```

## Example: content slide with all blocks

```markdown
## Slide 5 — 工夫① ディレクトリ構成

**話すこと:**

まず１つ目の工夫は、ディレクトリ構成です。このようになっています。

このディレクトリ構成の良い点は、スキルが個人やチームごとに整理されていて
誰がどんなスキルを持っているのかが一目でわかり、所有者が明確なことです。

**スライド要素:**

- ディレクトリツリー (下記)
- 補足ラベル: `p-*` = 個人 / `team-*` = チーム / CODEOWNERS で所有者明確化
- 対応コマンドのバッジ: `npx skills` / `gh skill`

\`\`\`
skills/
├── README.md
├── p-jackchuka/
│   └── skill-a/SKILL.md
└── ...
\`\`\`
```

## What the parser produces

`scripts/parse_md.py` outputs JSON like:

```json
{
  "title": "Agent Skills を社内で育てる仕組み作り",
  "slides": [
    {
      "index": 0,
      "number": 1,
      "subtitle": "タイトル",
      "notes": "",
      "elements": ["タイトル", "名前", "会社ロゴ"],
      "elements_raw": "- タイトル\n- 名前\n- 会社ロゴ",
      "raw_body": ""
    },
    {
      "index": 1,
      "number": 2,
      "subtitle": "自己紹介",
      "notes": "こんにちは、jackchuka と申します…",
      "elements": ["プロフィールアイコン", "..."],
      "elements_raw": "...",
      "raw_body": ""
    }
  ]
}
```

- `index` is zero-based position; `number` is the N from `## Slide N`.
- `notes` is the speaker-notes text, ready to push into the notes BODY shape.
- `elements` is the parsed bullet list (with leading `- `/`* ` stripped); `elements_raw` preserves the original markdown.
- `raw_body` captures any prose outside `**…**` blocks.

## Common authoring pitfalls

- **Hyphen vs em dash**: `## Slide 5 - foo` won't parse. Use `—`.
- **Missing `:**`**: `**話すこと**` without the trailing `:` doesn't match. The full marker is `**話すこと:**`.
- **Indented bullets** in `**スライド要素:**`: nested bullets are flattened by the parser. Reflect hierarchy in the text itself if you need it.
- **Code blocks** in 話すこと: preserved as-is, but speaker notes are plain text — formatting won't survive the push to Google Slides notes.
