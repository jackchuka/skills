---
name: p-news-briefing
license: MIT
description: Use when the user asks for news, wants a briefing, says "/news-briefing", or asks to aggregate recent information on any topic. Triggers on requests like "what's happening with AI", "get me news on crypto", "news briefing on climate".
allowed-tools: WebSearch Task Bash Write
argument-hint: "<topics> [--depth quick|deep]"
compatibility: Requires access to the internet
metadata:
  author: jackchuka
  scope: personal
  confirms:
    - save briefing to filesystem
  skillctx:
    version: "0.1.0"
---

# News Briefing

<!-- skillctx:begin -->
## Setup
Locate this skill's directory (the folder containing this SKILL.md), then run the
resolver script from there:

```bash
python <skill-dir>/scripts/skillctx-resolve.py resolve p-news-briefing
```

The resolver outputs each binding as `key: value` (one per line). Substitute each `{binding_key}` placeholder below with the resolved value.

If any values are missing or the user requests changes, use:
```bash
python <skill-dir>/scripts/skillctx-resolve.py set p-news-briefing <key> <value>
```
<!-- skillctx:end -->

Aggregate recent news on any topic(s) into structured markdown files.

## Invocation

- `/news-briefing ai, crypto` -- comma-separated topics
- `/news-briefing ai --depth quick` -- with explicit depth
- Conversational: "get me news on AI and crypto"

## Depth

- **deep** (default): News + market/people reactions, sourced links, quotes, ~5 min read
- **quick**: Headlines + brief context, 5-10 bullets with links, ~2 min read

## Flow

1. **Parse input**: Extract topic(s) and depth. Default depth is `deep`.
2. **Normalize topics**: Convert to URL-safe slugs for filenames (e.g., "artificial intelligence" -> `ai`, "open source" -> `open-source`).
3. **Create date directory**: `{notebook_daily_dir}YYYY-MM-DD/news/`
4. **Deduplicate against previous briefings** (parallelize if possible): Before researching, check for existing briefings on the same topic-slug in recent `daily/*/news/` directories (scan the last 14 days). Run dedup scans for all topics in parallel. Read any found files. Stories already covered in a previous briefing should be **skipped entirely** unless there is a meaningful follow-up (e.g., new data, reversal, sequel event). When a follow-up exists, write it as its own section and briefly note it builds on prior coverage — do not repeat the original story.
5. **Research directly** using WebSearch. Process all topics in parallel (parallelize if possible): after the dedup scan completes for all topics, dispatch all per-topic research tasks concurrently as a fan-out, then collect results and summarize.

### Per-Topic Research (parallelize if possible)

IMPORTANT: Recency is critical. Follow these rules strictly:

- **Always use today's exact date** (YYYY-MM-DD) to construct queries. Never use just a year or month alone.
- **Prefer "today", "yesterday", "past 24 hours", "past 48 hours"** in queries — these terms signal freshness to search engines far better than month/year.
- **Discard stale results**: After gathering search results, check publication dates. Only include stories from the **last 7 days** (for deep) or **last 3 days** (for quick). If a result has no visible date, deprioritize it.
- **If initial results are stale**, run follow-up queries with stricter time language (e.g., "today", "yesterday", site:reuters.com OR site:bloomberg.com).

**For deep depth:**

Phase 1 - Breaking/recent news: Run 3 WebSearch queries in parallel:

- "[TOPIC] news today [Full Month Day, Year]" (e.g., "AI news today February 6, 2026")
- "[TOPIC] latest news this week [Month Year]"
- "[TOPIC] breaking developments [Month Day Year]"

Phase 2 - Reactions & analysis: Run 2-3 WebSearch queries in parallel:

- "[TOPIC] market reaction today [Month Year]"
- "[TOPIC] social reaction today [Month Year]"
- "[TOPIC] analyst reaction [Month Day Year]"
- "[TOPIC] expert opinion latest [Month Year]"

Phase 3 - Fill gaps (only if needed): If Phase 1-2 returned fewer than 3 distinct stories, run 1-2 more targeted queries:

- "[TOPIC] [specific subtopic from earlier results] [Month Day Year]"
- site:reuters.com OR site:apnews.com "[TOPIC] [Month Year]"

**Graceful failure**: If a WebSearch query fails or returns no results, note the gap and continue with available data. Include a footer note in the output listing any failed queries so the reader knows coverage may be incomplete.

Phase 4 - Write output: Combine into structured markdown with:

- YAML frontmatter: topic, date, depth
- Major stories as H2 sections (each must include publication date)
- Market data (stock moves, valuations) where relevant
- Named quotes from analysts, CEOs, social media
- Inline source links as markdown hyperlinks
- A "Big Picture" H2 summary at the bottom

**For quick depth:**

Run 3 WebSearch queries in parallel:

- "[TOPIC] news today [Full Month Day, Year]"
- "[TOPIC] headlines this week [Month Year]"
- "[TOPIC] latest [Month Day Year]"

Then write a concise markdown file with:

- YAML frontmatter: topic, date, depth
- 5-10 bullet points, each a headline with 1-2 sentences of context
- Each bullet must include the publication date (e.g., "Feb 5")
- Inline source links as markdown hyperlinks
- Discard any results older than 3 days

### Output Format

```yaml
---
topic: Topic Name
date: YYYY-MM-DD
depth: deep
---
```

### Output Path

```
{notebook_daily_dir}YYYY-MM-DD/news/<topic-slug>.md
```

6. **Summarize**: After all topics are written, tell the user what files were created and give a one-line summary per topic.
