---
name: p-daily-standup
description: Aggregate previous business day activity and post standup update to Slack. Use when the user says "standup", "daily standup", "post status", "status update", or "/daily-standup".
argument-hint: "[--lang ja|en] [--dry-run]"
compatibility: Requires gh CLI, gws CLI, and Slack MCP server. Fireflies MCP server optional.
metadata:
  author: jackchuka
  scope: personal
  confirms:
    - post message to Slack
  skillctx:
    version: "0.1.0"
---

# Daily Standup

<!-- skillctx:begin -->
## Setup
Locate this skill's directory (the folder containing this SKILL.md), then run the
resolver script from there:

```bash
python <skill-dir>/scripts/skillctx-resolve.py resolve p-daily-standup
```

The resolver outputs each binding as `key: value` (one per line). Substitute each `{binding_key}` placeholder below with the resolved value.

If any values are missing or the user requests changes, use:
```bash
python <skill-dir>/scripts/skillctx-resolve.py set p-daily-standup <key> <value>
```
<!-- skillctx:end -->

Aggregate activity from the previous business day (GitHub, Slack, Calendar, Meetings) and post a status update to the `{channel_name}` Slack thread.

## When to Use

- User says "standup", "daily standup", "post status update", "status update"
- User invokes `/daily-standup`

## Prerequisites

- `gh` CLI authenticated (`gh auth status`)
- `gws` CLI installed (Google Calendar)
- Slack MCP connected
- Fireflies MCP connected (optional — skip gracefully if unavailable)

## Arguments

- `--lang ja|en` — Language for bullet points. Default: `ja`. Ask user if not specified.
- `--dry-run` — Draft only, do not post to Slack.

## Workflow

### Phase 1: Initialize

1. Parse arguments for `--lang` and `--dry-run`.
2. If language not specified, ask: "Japanese or English for today's standup? (default: Japanese)"
3. Compute dates:
   - **Previous business day**: If today is Monday, use last Friday. Otherwise use yesterday. Format as `YYYY-MM-DD`.
   - **Today**: Format as `YYYY-MM-DD`.
4. Call `slack_read_user_profile()` (no args) to get the current user's Slack ID.

### Phase 2: Find Today's Thread

1. Call `slack_read_channel` on channel `{channel_id}` with `limit: 20`.
2. Filter messages to only those from user `USLACKBOT` whose timestamp falls on **today's date** (convert Unix `ts` to date and compare).
3. From the filtered messages, find the one whose text contains **"share your status in the thread"** — this is the daily standup reminder thread.
4. Save the `ts` of that message as `thread_ts` for posting later.
5. If no matching thread found: warn user and offer to output draft only.

### Phase 3: Aggregate やったこと (parallelize if possible)

**Shared context** (passed to all sub-tasks):
- `PREV_BIZ_DAY`: previous business day (YYYY-MM-DD)
- `TODAY`: today's date (YYYY-MM-DD)
- `LANG`: output language (ja | en)
- `USER_ID`: Slack user ID (from `slack_read_user_profile` in Phase 1)
- `THREAD_TS`: standup thread timestamp from Phase 2

Dispatch all four sub-tasks (3a–3d) concurrently. If your platform supports parallel subagents, launch one per source. Otherwise, query each sequentially. Wait for all four to return before Phase 5.

#### 3a. GitHub Activity
→ See `references/agent-gather-github-prev-day.md`

#### 3b. Slack Activity
→ See `references/agent-gather-slack-prev-day.md`

#### 3c. Calendar (gws CLI)
→ See `references/agent-gather-calendar-prev-day.md`

#### 3d. Meetings (Fireflies MCP)
→ See `references/agent-gather-fireflies-prev-day.md`

### Phase 4: Aggregate やること (parallelize if possible)

Run in parallel:

#### 4a. Open GitHub Work
→ See `references/agent-gather-github-open-work.md`

#### 4b. Today's Calendar

```bash
gws calendar +agenda --today
```

Extract meeting names for today.

### Phase 5: Draft Message

1. Compose the standup message in the chosen language (translate if needed).
2. Format:

```
やったこと
• [item 1]
• [item 2]
やること
• [item 1]
• [item 2]
```

3. Deduplication rules:
   - A PR that appears in both "authored" and "merged" → show once as merged
   - A meeting that overlaps with a GitHub PR discussion → keep both but don't repeat the same topic
   - Slack messages about a PR already listed → skip

4. Ordering:
   - やったこと: PRs first, then meetings, then other Slack activity
   - やること: Open PRs first, then reviews requested, then today's meetings

5. Keep bullets concise — one line per item, no sub-bullets.

### Phase 6: Confirm and Post

1. Present the draft to the user:

```
Here's your standup draft:

---
やったこと
• ...
やること
• ...
---

Post to {channel_name} thread? (yes/edit/cancel)
```

2. If user says **edit**: ask what to change, revise, re-confirm.
3. If user says **yes**: post via Slack MCP:

```
slack_send_message(channel_id="{channel_id}", message="<the message>", thread_ts="<thread_ts from Phase 2>")
```

4. If user says **cancel** or `--dry-run` was set: output the draft and stop.
5. After posting, confirm with the permalink.

## Error Handling

| Error | Action |
|-------|--------|
| No Slackbot thread today | Warn user, offer draft-only mode |
| `gws` not installed | Skip calendar, note in output |
| Fireflies unavailable | Skip meeting summaries, note in output |
| `gh` auth failure | Warn user, suggest `gh auth login` |
| No activity found | Tell user "no activity found for [date]" |
| Slack send fails | Show error, output draft for manual posting |
