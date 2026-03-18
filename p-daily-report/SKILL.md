---
name: p-daily-report
description: Use when reviewing what you worked on, creating standups, writing status updates, tracking daily/weekly progress, or asking "what did I do today"
allowed-tools:
  - Read
  - Bash
  - Write
argument-hint: "[--days N] [--yesterday] [--project NAME] [--summary]"
compatibility: Requires gh CLI, gws CLI, and Slack MCP server
metadata:
  author: jackchuka
  scope: personal
  confirms:
    - save report to filesystem
  skillctx:
    version: "0.1.0"
---

# Daily Report Generator

<!-- skillctx:begin -->
## Setup
Locate this skill's directory (the folder containing this SKILL.md), then run the
resolver script from there:

```bash
python <skill-dir>/scripts/skillctx-resolve.py resolve p-daily-report
```

The resolver outputs each binding as `key: value` (one per line). Substitute each `{binding_key}` placeholder below with the resolved value.

If any values are missing or the user requests changes, use:
```bash
python <skill-dir>/scripts/skillctx-resolve.py set p-daily-report <key> <value>
```
<!-- skillctx:end -->

Generate activity reports from Claude Code conversation history, GitHub activity, and Slack messages.

**IMPORTANT output rule**: The generated report file must never mention "Claude", "Claude Code", "sessions", "history.jsonl", or any implementation details about how the data was gathered. The report should read as a clean, source-agnostic activity log. This rule applies only to the written output — these skill instructions may freely reference Claude internals.

## When to Use

- End of day/week summaries
- Standup prep
- Status updates for stakeholders
- Tracking accomplishments across projects

## Options

- `--days N` or number: Last N days (default: today)
- `--yesterday`: Yesterday only
- `--project NAME`: Filter by project
- `--summary`: Add project summary table

## Date Range Reference

Determine `{date}` and `{next_date}` from options. Get today's date with `date +%Y-%m-%d`.

| Option          | `{date}`   | `{next_date}` |
| --------------- | ---------- | ------------- |
| default (today) | today      | tomorrow      |
| `--yesterday`   | yesterday  | today         |
| `--days N`      | N days ago | tomorrow      |

## Steps

### Parallel Initialization

Before gathering data, check tool availability concurrently (parallelize if possible):

```bash
# Run all three concurrently
gh api /user --jq '.login'      # confirms gh is authenticated; capture as gh_user
gws calendar +agenda --today    # confirms gws is available (or note unavailable)
slack_read_user_profile          # confirms Slack MCP is connected (or note unavailable)
```

Use results to skip unavailable data sources in subsequent steps.

### Aggregate Claude Activity

**Location:** `{claude_history_path}`

If this file doesn't exist or is empty, skip this step and proceed to GitHub activity.

**Format:** JSONL with fields:

- `timestamp`: Unix milliseconds → convert to local date
- `project`: Full path → extract last segment as name
- `display`: User's message
- `sessionId`: Groups related work

#### Reading Entries

1. Get line count: `wc -l {claude_history_path}`
2. Read a generous buffer: `offset=(lines - 3000)` to cover ~2 weeks of activity
3. Filter entries by timestamp — convert `timestamp` (Unix ms) to local date, compare against target date range, discard entries outside the range

#### Extract GitHub Repos from Project Paths

Project paths using `ghq` convention contain the `owner/repo`:

```
/Users/*/ghq/github.com/{owner}/{repo} → {owner}/{repo}
```

Extract with pattern: match `github.com/` then take the next two path segments.

- Build a map of `owner/repo` → project display name
- Non-GitHub project paths (e.g., `~/notes/project-x`) have no repo — keep them for the report as local projects, skip them for GitHub queries

#### Filter Noise

Remove:

- Slash commands (`/clear`, `/model`, etc.)
- Single responses: "yes", "no", "1", "2", "a", "b"
- Empty/duplicate entries

#### Summarize by Session

Group same-sessionId entries into meaningful summaries:

| Raw Messages                       | Summary                      |
| ---------------------------------- | ---------------------------- |
| "fix lint", "yes", "run tests"     | Working on linting and tests |
| "implement X", "yes", "continue"   | Implementing X feature       |
| "investigate bug", "this error..." | Debugging issues             |

#### Categorize

Tag with: **feat**, **fix**, **refactor**, **docs**, **test**, **ci**, **plan**

---

Steps 2, 3, and 4 are independent data sources. Dispatch all three concurrently (parallelize if possible). Proceed to Output only after all three complete.

---

### Get GitHub Activity (parallelize if possible)

→ See `references/agent-gather-github-report.md`

If `gh` is not installed or not authenticated, skip this step and note in the report.

### Get Google Calendar (parallelize if possible)

→ See `references/agent-gather-calendar-report.md`

If `gws` is not installed, skip this step and omit the Calendar section from the report.

### Get Slack Activity (parallelize if possible)

→ See `references/agent-gather-slack-report.md`

If the Slack MCP server is not connected, skip this step and omit the Slack section from the report.

---

**SYNC: Proceed to Output only after all data gathering steps complete.**

**Deduplicate**: Before formatting, deduplicate across sources — the same PR may appear in both GitHub API results and Slack messages. Use PR URLs as primary keys to merge overlapping records.

---

### Output Format

```yaml
---
date: YYYY-MM-DD
type: daily-report
---
```

```markdown
# Daily Activity Report YYYY-MM-DD

## Calendar

- 14:30 Design review
- 16:00 1:1 with manager

## owner/repo-name

Implemented user authentication and fixed pagination bug. Added logout button
and improved empty state handling.

- PR #12 Add status line styles [merged]
- Review #45 Cleanup implementation [APPROVED]

## notebook

Worked on meeting notes and snippets conversion.

## Slack

- **#eng**: Discussed deployment rollback strategy and shared post-mortem findings
- **#project-x**: Reviewed design mockups and confirmed timeline for v2 launch

## Other Repositories

- Review myorg/repo#5 bump time dep [APPROVED]
- Issue myorg/other-repo#10 Bug report [open]
```

**Per-project format:**

1. **Summary** (required): 1-3 sentences synthesized from all sources (Claude history, commit messages, PR descriptions). Written as prose, no tags or prefixes. Captures _what you did_, not how the data was gathered.
2. **PRs and reviews** (optional): Listed below the summary only when they exist. No subheader — just the items. Format: `- PR #N title [state]` or `- Review owner/repo#N title [STATE]`.
3. If a project has no PRs or reviews, it's summary-only.

**Other rules:**

- Non-GitHub projects from Claude history use their directory name as the section header (e.g., "notebook").
- Items from GitHub that don't match any known project go under "Other Repositories".
- Omit any section that has no activity.
- No `[tag]` prefixes, no commit hashes, no "N commits pushed".

### Output Path

1. **Create date directory**: `mkdir -p {notebook_daily_dir}/YYYY-MM-DD/`
2. **Write report file**: `{notebook_daily_dir}/YYYY-MM-DD/report.md`
   - For multi-day reports: `{notebook_daily_dir}/YYYY-MM-DD/report-N-days.md`
3. **Summarize**: After writing, tell the user the file path and give a brief overview of what was captured.

## Summary Table (with --summary)

```markdown
| Project | Days Active | Activities | PRs | Reviews | Top Focus |
| ------- | ----------- | ---------- | --- | ------- | --------- |
| my-proj | 5           | 45         | 3   | 2       | feat, fix |
```
