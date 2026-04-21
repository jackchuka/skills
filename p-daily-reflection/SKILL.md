---
name: p-daily-reflection
license: MIT
description: >
  Reflect on past work and iterate to improve. Analyzes Claude sessions, GitHub,
  Slack, and Fireflies to generate a journal entry with actionable improvements.
  Updates persistent memory with confirmed learnings.
  Use when the user says "reflect", "reflection", "what can I improve",
  "retrospective", "review my work", or "/daily-reflection".
argument-hint: "[--days N] [--since YYYY-MM-DD] [--skip-memory]"
compatibility: Requires gh CLI. Slack MCP and Fireflies MCP servers optional.
metadata:
  author: jackchuka
  scope: personal
  confirms:
    - save to filesystem
    - update memory files
  skillctx:
    version: "0.1.0"
---

# Daily Reflection

<!-- skillctx:begin -->
## Setup
Locate this skill's directory (the folder containing this SKILL.md), then run the
resolver script from there:

```bash
python <skill-dir>/scripts/skillctx-resolve.py resolve p-daily-reflection
```

The resolver outputs each binding as `key: value` (one per line). Substitute each `{binding_key}` placeholder below with the resolved value.

If any values are missing or the user requests changes, use:
```bash
python <skill-dir>/scripts/skillctx-resolve.py set p-daily-reflection <key> <value>
```
<!-- skillctx:end -->

Reflect on past work and iterate to improve. Gathers activity from Claude sessions, GitHub, Slack, and Fireflies, then analyzes through reflection lenses to produce a journal with actionable improvements. Reads previous reflections to track follow-through and detect recurring patterns. Updates persistent memory so learnings feed back into future sessions.

## Arguments

- `--days N` — look back N days (default: 1)
- `--since YYYY-MM-DD` — reflect from a specific date
- `--skip-memory` — generate journal only, don't update `.claude/` memory

## Steps

### Step 0: Setup

Resolve all inputs into concrete variables before any other step runs.

**Date range:**
1. If `--since YYYY-MM-DD` provided: `REFLECT_START = <that date>`, `REFLECT_END = today`
2. If `--days N` provided: `REFLECT_START = today minus N days`, `REFLECT_END = today`
3. Default: `REFLECT_START = today`, `REFLECT_END = today` (last 24 hours)

Set `REFLECT_START` and `REFLECT_END` as `YYYY-MM-DD` strings. Derive `REFLECT_END_PLUS_1` (one day after `REFLECT_END`, used in Slack queries).

**Flags:**
- `SKIP_MEMORY` = `true` if `--skip-memory` was passed, otherwise `false`

All subsequent steps use these variables. Do not re-derive them.

### Step 1: Read Previous State

Before gathering new data, read two files:

1. **Previous reflection journal**: Find the most recent `reflection.md` in `{notebook_daily_dir}`. Scan date-stamped directories in reverse order to find the last one that contains a `reflection.md`. Extract:
   - Action items (checked and unchecked)
   - Key themes and patterns noted

2. **Memory file**: Read `{reflections_memory_path}` (if it exists). This contains confirmed learnings from past reflections.

Store both for use in Step 3 (analysis) and Step 4 (output).

### Step 2: Gather Activity (Parallel)

Launch four Agent tool calls in parallel — one per data source. Each agent returns structured observations. If a source is unavailable (e.g., no Fireflies server), the agent must return the standard empty-result envelope:

```json
{"source": "<name>", "status": "unavailable", "observations": []}
```

#### 2a: Claude Code History
→ See `references/agent-gather-claude-history.md`

#### 2b: GitHub Activity
→ See `references/agent-gather-github.md`

#### 2c: Slack Activity
→ See `references/agent-gather-slack.md`

#### 2d: Fireflies Meetings
→ See `references/agent-gather-fireflies.md`

### Step 2.5: Aggregate

After all four agents complete, collect and consolidate their outputs before analysis.

1. **Collect all outputs** into a unified structure:
   ```
   {
     "claude_history": <2a output or empty-result envelope>,
     "github":         <2b output or empty-result envelope>,
     "slack":          <2c output or empty-result envelope>,
     "fireflies":      <2d output or empty-result envelope>
   }
   ```
   Any agent that returned `{"source": "...", "status": "unavailable", "observations": []}` is recorded as-is — do not attempt to re-fetch.

2. **Deduplicate cross-source events** by primary key:
   - PRs: use the PR URL as the primary key — if the same PR appears in both GitHub data and Slack messages, merge into one record.
   - Commits: use the commit SHA as the primary key — if the same commit appears in both GitHub and Claude history project references, keep one entry.
   - Meetings: use the Fireflies meeting ID — if a meeting is referenced in both Fireflies and Slack, merge.

3. **Note missing sources**: For any source with `"status": "unavailable"`, record it in the aggregate so downstream lenses can acknowledge the gap rather than silently skip it.

Proceed to Step 3 only after this aggregate is complete.

### Step 3: Analyze Through Reflection Lenses

After all agents return, analyze the combined data through five lenses. For each lens, produce **0–3 concrete observations**. If a lens has no meaningful signal, skip it entirely — do not force insights.

#### Lens 1: Skill Health

Using slash command and skill invocation data from Step 2a:

- Which skills were used and how often?
- Any skills abandoned mid-use (session shows `/skill-name` but no completion)?
- Any skills that errored (error entries shortly after a slash command)?
- Skills not used during this period but used in previous reflections — are they forgotten or no longer needed?

#### Lens 2: Recurring Friction

Cross-reference all four data sources to find repeated pain points:

- Same error appearing in multiple Claude sessions
- Repeated manual steps that could be automated (same sequence of commands across sessions)
- Knowledge-gap questions on Slack ("how do I…", "where is…") that indicate missing docs or tooling
- Blockers raised in Fireflies meetings that reappear in later meetings

Compare against the previous reflection from Step 1. If a friction point was noted before, flag it as **recurring** — it needs escalation or a different approach.

#### Lens 3: Decision Quality

Cross-reference Slack and Fireflies with GitHub to check follow-through:

- Meeting commitments ("I'll do X by Friday") — did corresponding commits or PRs appear?
- Slack decisions ("let's go with approach B") — is there evidence of execution?
- Scope changes — did the actual work (commits) match the stated plan, or did scope shift?

#### Lens 4: Learning Patterns

From Claude Code history corrections and debugging sequences:

- **New techniques tried** — first-time use of a tool, library, or approach
- **Corrections made** — cases where the user suggested X, then corrected to Y (indicates a learning moment or a tool gap)
- **Multi-step debugging breakthroughs** — long debugging sessions that eventually resolved (what was the key insight?)

#### Lens 5: Follow-Through

Using the previous reflection's action items from Step 1:

- **Addressed** — search commits, PRs, and Slack messages for evidence that the action item was completed
- **Outstanding** — action items with no evidence of progress
- **Meeting commitments not acted on** — promises from Fireflies that have no matching activity in GitHub or Slack

### Step 4: Generate Journal Entry

Write the reflection journal to `{notebook_daily_dir}/YYYY-MM-DD/reflection.md` (create the directory if needed).

Format:

```markdown
# Reflection — YYYY-MM-DD

## What happened
Brief narrative (3-5 sentences) of the day's work across all projects. Synthesize from all sources — don't list sources. Write as if journaling, not reporting.

## What I learned
- Bullet list from Lens 4 (Learning Patterns)
- Include new techniques, debugging insights, corrections

## What went well
- Effective patterns observed
- Good decisions that played out well
- Smooth workflows, skills that worked great

## What didn't
- Friction points from Lens 2
- Failed approaches, time sinks
- Scope mismatches from Lens 3

## Skill health
- Observations from Lens 1 (only include if meaningful signal)

## Action items
- [ ] Concrete, actionable improvements (from all lenses)
- [ ] Each item should be doable in a single session
- [ ] Maximum 5 items — prioritize by impact

## Follow-through
- [x] Items from previous reflection that were completed (Lens 5)
- [ ] Items still outstanding — carried forward with context
```

Rules:
- Never mention "Claude", "Claude Code", "sessions", "MCP", or implementation details — source-agnostic prose
- Don't force sections — skip any with no meaningful content
- Action items must be specific ("refactor X in file Y") not vague ("improve code quality")
- If reflecting over multiple days (`--days N`), organize "What happened" chronologically

### Step 5: Update Memory

Unless `SKIP_MEMORY` is `true` (set in Step 0), update persistent memory.

**Memory file:** `{reflections_memory_path}`

**What to write:** Only learnings meeting the confirmation threshold:
- Pattern observed 2+ times across reflections (check previous entries)
- Explicit correction that should never be repeated
- Skill improvement that was validated

**Entry format:**
```
### YYYY-MM-DD: [Brief title]
- [One-line learning or pattern]
```

**Maintenance rules:**
- Cap at ~100 lines. Remove oldest irrelevant entries when exceeded.
- Deduplicate — if new learning is more specific version of existing, replace old.
- Don't write speculative observations. Single-occurrence patterns stay in journal only.

**First-run setup:**
1. If `reflections.md` doesn't exist, create with header: `# Reflection Learnings\n\nConfirmed patterns and learnings from daily reflections.\n`
2. If `MEMORY.md` exists in same dir, append reference: `- See reflections.md for accumulated learnings from daily reflections`
3. If `MEMORY.md` doesn't exist, create with just that reference line.

**Announce completion:**
- "Reflection saved to {notebook_daily_dir}/YYYY-MM-DD/reflection.md"
- "N new learnings added to memory" (or "No new learnings met the confirmation threshold")
- List the action items generated
