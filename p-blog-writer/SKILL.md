---
name: p-blog-writer
description: >
  Write blog posts in {user_name}'s voice with theoretical depth and persuasive arguments.
  Iterative workflow: intake → outline → section-by-section expansion → polish.
  Adapts to tool announcements, opinion pieces, deep-dives, and tutorials.
  Use when the user says "/blog-writer", "write a blog post", "draft an article about",
  "help me write about", or wants to create blog content.
argument-hint: "<topic> [--type tool|opinion|deep-dive|tutorial] [--platform {default_platform}|{alt_platform}]"
compatibility: NA
metadata:
  author: jackchuka
  scope: personal
  confirms:
    - save draft to filesystem
  skillctx:
    version: "0.1.0"
---

# Blog Writer

<!-- skillctx:begin -->
## Setup
Locate this skill's directory (the folder containing this SKILL.md), then run the
resolver script from there:

```bash
python <skill-dir>/scripts/skillctx-resolve.py resolve p-blog-writer
```

The resolver outputs each binding as `key: value` (one per line). Substitute each `{binding_key}` placeholder below with the resolved value.

If any values are missing or the user requests changes, use:
```bash
python <skill-dir>/scripts/skillctx-resolve.py set p-blog-writer <key> <value>
```
<!-- skillctx:end -->

Write blog posts that sound like {user_name} — casual-professional Japanese with natural English technical terms — while strengthening theoretical depth and persuasion.

## When to Use

- User wants to write a blog post or article
- User has a topic idea and wants it turned into a draft
- User has notes or an outline and wants it expanded
- User says "/blog-writer" or "write a blog post about X"

## Prerequisites

- Voice profile: `{voice_profile_path}` (read this FIRST before any writing)
- Output directory: `{blog_drafts_dir}`

## Arguments

- Topic, idea, or notes (required — can be a single phrase or detailed notes)
- `--type <tool|opinion|deep-dive|tutorial>` (optional — auto-detected if omitted)
- `--platform <{default_platform}|{alt_platform}>` (optional — defaults to {default_platform})
- `--audience <description>` (optional — e.g., "Go developers", "junior engineers")

## Workflow

### Step 1: Intake

1. Read `{voice_profile_path}` to internalize the voice and persuasion patterns.

2. Parse the user's input:
   - If just a topic/idea: proceed with what's given
   - If topic + audience + takeaway: use all three to shape the article
   - If notes/outline: use as the starting structure

3. Detect article type from the input:
   - **Tool announcement**: user mentions building/releasing something ("〜を作った", "I built X")
   - **Opinion/essay**: user has a claim or position ("why X matters", "X is underrated")
   - **Deep-dive/comparison**: user wants to explain or compare ("how X works", "X vs Y")
   - **Tutorial/guide**: user wants to teach ("how to set up X", "complete guide to X")
   - User can override with `--type`

4. If the input is thin (just a few words), ask 1-2 clarifying questions:
   - "Who is the target reader for this post?"
   - "What's the one thing you want the reader to take away?"
   - Do NOT ask more than 2 questions. Work with what you have.

### Step 2: Outline with Argument Structure

Generate a structured outline based on article type.

#### Tool Announcement Outline

```
## タイトル: [title]

### 1. 背景 / Pain Point
- [Concrete problem] — persuasion: Stakes
- "〜していませんか？" or "〜で困ったことはありませんか？"

### 2. ツール紹介
- What it does (1-2 sentences)
- Installation command

### 3. 使い方
- Basic usage with CLI examples
- Key features with output examples

### 4. 設計思想 (Design Philosophy)
- Why these design decisions — persuasion: Contrast Framing
- Trade-offs acknowledged — theory anchor
- Underlying principles

### 5. 「でも〜では？」(Objection Handling)
- Anticipate 1-2 objections and address them
- Compare with alternatives fairly

### 6. まとめ
- Key takeaway
- Links to repo
- Call to action (Star, feedback)
```

#### Opinion/Essay Outline

```
## タイトル: [title]

### 1. Hook
- Bold claim or surprising observation — persuasion: Stakes

### 2. Evidence
- 2-3 concrete examples or data points — persuasion: Evidence

### 3. Why This Is True
- Underlying principle or theory — theory anchor
- Analogy to something familiar — persuasion: Analogy Bridge

### 4. Counter-argument
- Strongest objection — persuasion: Objection Handling
- Why you still believe your claim

### 5. Implications
- What this means for the reader's work

### 6. まとめ
- Restate core insight
- Call to action or question for the reader
```

#### Deep-Dive/Comparison Outline

```
## タイトル: [title]

### 1. Context & Framing
- Why this topic matters now — persuasion: Stakes

### 2. Concept Explanation
- Core concept with analogy — persuasion: Analogy Bridge
- How it works (theory depth)

### 3. Detailed Analysis
- Technical details with examples
- Code or architecture walkthrough

### 4. Trade-offs
- Comparison matrix or table — persuasion: Contrast Framing
- When to use what

### 5. Recommendation
- Author's pick with reasoning — persuasion: Evidence

### 6. まとめ
```

#### Tutorial/Guide Outline

```
## タイトル: [title]

### 1. Who This Is For
- Target audience and prerequisites

### 2-N. Progressive Sections
- Basic → Intermediate → Advanced
- Each with practical examples and code
- Persuasion: Evidence (show results at each step)

### N+1. Common Pitfalls
- What to watch out for — persuasion: Objection Handling

### N+2. まとめ
- Next steps and further reading
```

After generating the outline:

1. Ask 1-2 sharpening questions:
   - "この記事で読者が感じる最大の反論は何ですか？" (What's the biggest objection a reader would have?)
   - "読者に一番覚えてほしいことは？" (What's the one thing you want readers to remember?)
   - Only ask if the answers aren't already obvious from the input.

2. Present the outline and wait for approval. User can:
   - Approve as-is
   - Request changes (reorder, add/remove sections, change angle)
   - Provide answers to sharpening questions

### Step 3: Section-by-Section Expansion

For each section in the approved outline:

1. Write the section in Japanese, following the voice profile:
   - Apply the persuasion pattern assigned to that section
   - Include code blocks, CLI examples, or output where relevant
   - Add theory depth at marked theory anchors
   - Keep the casual-professional tone — no academic language

2. Present the section and ask:
   - "この section はどうですか？ approve / revise / 別のアングルで rewrite"
   - If revise: ask what to change
   - If rewrite: try a different persuasion angle or framing

3. Move to the next section after approval.

### Step 4: Polish & Save

1. Assemble all approved sections into a single markdown file.

2. Add platform frontmatter:

   **For Zenn:**
   ```yaml
   ---
   title: "[title]"
   emoji: "[relevant emoji]"
   type: "tech"
   topics: ["topic1", "topic2"]
   published: false
   ---
   ```

   **For Qiita:**
   ```yaml
   ---
   title: "[title]"
   tags:
     - tag1
     - tag2
   private: true
   ---
   ```

3. Generate slug from title (lowercase, hyphens, ASCII only).

4. Save to `{blog_drafts_dir}{slug}.md`.

5. Show the complete draft to the user for final review.

6. Report: "Draft saved to `{blog_drafts_dir}{slug}.md`"

## Privacy & Safety

- Never include real company names, internal URLs, or secrets in blog content
- If writing about work-related topics, generalize and anonymize
- Don't publish — always save as draft with `published: false` or `private: true`

## Examples

### Example 1: Tool announcement

User: "mdschemaを作った話を書きたい"

→ Detects: tool announcement
→ Generates outline with design philosophy section and objection handling
→ Iterates section by section
→ Saves to `{blog_drafts_dir}mdschema-wo-tsukutta-hanashi.md`

### Example 2: Opinion piece

User: "write a blog post about why Go interfaces are underrated"

→ Detects: opinion/essay
→ Generates outline with bold hook, evidence, counter-argument
→ Asks: "最大の反論は何？"
→ Iterates and saves

### Example 3: Minimal input

User: "blog about goroutines"

→ Input is thin — asks: "対象読者は？" and "takeaway は？"
→ User answers → detects deep-dive
→ Proceeds with outline
