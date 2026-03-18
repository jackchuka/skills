---
name: p-blog-post-mining
description: >
  Mine development activities for blog-worthy topics and create outlines.
  Analyzes Claude session history, GitHub commits/PRs, Slack discussions,
  and Fireflies meeting recordings to find interesting stories.
  Use when the user wants blog ideas, content inspiration, or asks
  "what can I write about", "find blog material", "blog ideas from my work",
  "/blog-post-mining".
argument-hint: "[--days N] [--audience <target>] [--topic <filter>]"
compatibility: Requires gh CLI. Slack MCP and Fireflies MCP servers optional.
metadata:
  author: jackchuka
  scope: personal
  confirms:
    - save to filesystem
  skillctx:
    version: "0.1.0"
---

# Blog Post Mining

<!-- skillctx:begin -->
## Setup
Locate this skill's directory (the folder containing this SKILL.md), then run the
resolver script from there:

```bash
python <skill-dir>/scripts/skillctx-resolve.py resolve p-blog-post-mining
```

The resolver outputs each binding as `key: value` (one per line). Substitute each `{binding_key}` placeholder below with the resolved value.

If any values are missing or the user requests changes, use:
```bash
python <skill-dir>/scripts/skillctx-resolve.py set p-blog-post-mining <key> <value>
```
<!-- skillctx:end -->

Analyze recent development activities across multiple sources to discover blog-worthy topics, then produce structured outlines ready for writing.

## When to Use

- User asks for blog ideas or content inspiration
- User wants to turn recent work into blog posts
- User says "what can I write about" or "find blog material"
- User wants to identify stories from their development activities

## Prerequisites

- `{claude_history_path}` exists (Claude Code session history)
- `gh` CLI installed and authenticated (GitHub activity)
- Slack MCP server configured (Slack discussions)
- Fireflies MCP server configured (meeting recordings, optional)

## Arguments

Parse from the user's invocation:

- **Time range**: "past N days/weeks/month" (default: past 14 days)
- **Audience**: "company blog", "personal blog", "tech community", "dev.to" (default: personal)
- **Language**: output language for outlines (default: same as user's message)
- **Topic filter**: optional focus area (e.g., "AI", "tooling", "architecture")

## Workflow

### Step 1: Gather Raw Activity (parallelize if possible)

All four sources are independent. Dispatch all four data collection tasks concurrently (parallelize if possible). If your platform supports parallel subagents, launch one per source. Otherwise, query each sequentially. Wait for all sources to return before proceeding to Step 2.

**Source 1 — Claude Session History:**

Read `{claude_history_path}` and filter entries by timestamp for the target date range.

Group by `sessionId` and extract:

- First prompt per session (the task goal)
- Number of messages per session (complexity indicator)
- Project path (what repo/area was involved)

Focus on sessions with 5+ messages — these represent substantial work, not quick one-offs.

**Source 2 — GitHub Activity:**

```bash
gh api graphql -f query='
query {
  viewer {
    contributionsCollection(from: "{start_date}T00:00:00Z", to: "{end_date}T00:00:00Z") {
      commitContributionsByRepository {
        repository { nameWithOwner description }
        contributions { totalCount }
      }
      pullRequestContributions(first: 50) {
        nodes {
          pullRequest {
            title body url state number
            repository { nameWithOwner }
          }
        }
      }
    }
  }
}'
```

For repos with significant commit counts, fetch commit messages:

```bash
gh api "repos/{owner}/{repo}/commits?author={user}&since={start}&until={end}" \
  --jq '.[] | "\(.commit.message | split("\n") | .[0])"'
```

**Source 3 — Slack Discussions:**

Use Slack MCP tools:

1. Call `slack_read_user_profile()` (no args) to get the current user's ID
2. `slack_search_public_and_private` with `"from:me after:{start_date}"` — find substantive messages you wrote
3. Focus on threads with 5+ replies (indicates discussion-worthy topics)

**Source 4 — Fireflies Meetings (if available):**

1. `fireflies_get_transcripts` for the date range
2. `fireflies_get_summary` for each meeting (parallelize if possible — each call is independent) — look for decisions, debates, and interesting topics discussed

**SYNC**: Wait for all sources to return before proceeding. If a source is unavailable (e.g., no Fireflies MCP server, `gh` not authenticated), skip it and note the omission — do not fail the entire gathering step.

**Deduplicate**: Before analysis, deduplicate across sources — the same PR may appear in both GitHub and Slack data, the same topic may surface in both Claude history and a meeting. Use PR URLs and commit SHAs as primary keys.

### Step 2: Identify Blog-Worthy Stories

Analyze collected data through these lenses:

**Story Types** (check each against the data):

| Type                  | Signal                                                          | Example                                                       |
| --------------------- | --------------------------------------------------------------- | ------------------------------------------------------------- |
| Problem-Solution      | Multiple sessions debugging the same issue, then a breakthrough | "How I debugged TUI spinner animation across 5 sessions"      |
| Tool/Process Creation | New tool built from scratch (new-tool-kickoff flow)             | "Building a CLI restaurant finder with Go + HotPepper API"    |
| Architecture Decision | Significant design choice with trade-offs discussed             | "Why we chose CQRS for our ERP module framework"              |
| Failure Story         | Repeated attempts, wrong approaches, eventual resolution        | "What I learned from trying to mock APIs with LLMs"           |
| Workflow Optimization | Creating a skill/automation that saves recurring effort         | "Automating OSS releases across 13 repos with a Claude skill" |
| Team Practice         | Process or convention established across the team               | "Introducing spec-driven development with erp-kit"            |
| Comparison/Evaluation | Research sessions comparing tools or approaches                 | "Comparing TUI frameworks for Git repository visualization"   |

**Scoring criteria** (internal, don't show to user):

- **Depth**: How many sessions/commits were spent? More = richer story
- **Novelty**: Is this a common blog topic or something unusual?
- **Lessons**: Were there failures, pivots, or non-obvious insights?
- **Audience appeal**: Would others face similar challenges?

### Step 3: Present Candidates

Show the top 5-8 candidates as a numbered list:

```
Blog Post Candidates:

1. [Title] — [1-line pitch]
   Sources: [which data sources contributed]
   Depth: [how much material is available]

2. [Title] — [1-line pitch]
   Sources: [sources]
   Depth: [depth]

...
```

Group by story type if there are many candidates.

Ask: **"Which topics interest you? (e.g., '1, 3, 5' or suggest your own angle)"**

### Step 4: Create Outlines

If multiple topics are selected, generate all outlines concurrently (parallelize if possible) — each outline is independent.

For each selected topic, generate a structured outline:

```markdown
# [Blog Post Title]

## Angle

[1-2 sentences: what's the unique perspective or takeaway]

## Target Audience

[Who would read this and why]

## Outline

### Introduction

- [Hook: the problem or situation that draws the reader in]
- [Why this matters]

### [Section 1: Context/Setup]

- [Key points from the gathered data]

### [Section 2: The Journey/Process]

- [What happened, what was tried]
- [Include specific details from sessions/commits — sanitized]

### [Section 3: Solution/Insight]

- [What worked and why]
- [Code snippets or architecture decisions if relevant]

### [Section 4: Lessons Learned]

- [What would you do differently]
- [Advice for others facing similar challenges]

### Conclusion

- [Key takeaway]
- [Call to action or next steps]

## Supporting Material

- [Relevant PRs/commits that could be referenced]
- [Related tools or links]

## Estimated Length

[Short (800-1200 words) / Medium (1500-2500 words) / Long (3000+ words)]
```

### Step 5: Save Outlines

Write each outline to:

```
{blog_drafts_dir}/{topic-slug}.md
```

Create the directory if it doesn't exist. Report the file paths to the user.

## Privacy and Safety

- Never include raw session content, secrets, or internal URLs in outlines
- Sanitize company-specific details unless the user confirms it's for a company blog
- Replace specific names with roles (e.g., "a teammate" instead of actual names)
- Paraphrase rather than quote verbatim from history

## Examples

**Example 1: General mining**

```
User: "/blog-post-mining"
Action: Analyze past 14 days across all sources, find 5-8 candidates, present list
```

**Example 2: Focused mining**

```
User: "find blog material about AI tooling from the past month"
Action: Analyze past 30 days, filter for AI/tooling topics, find candidates
```

**Example 3: Company blog**

```
User: "any blog material for our company blog? past 2 weeks"
Action: Analyze past 14 days, focus on team-relevant topics, adjust tone for company audience
```

**Example 4: From a specific project**

```
User: "blog ideas from working on <project name> this month"
Action: Filter history for <project name> project sessions, analyze the build journey
```
