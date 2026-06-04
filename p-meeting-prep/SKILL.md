---
name: p-meeting-prep
license: MIT
description: Generate per-meeting prep briefs for today's calendar. Use when the user says "meeting prep", "prep my meetings", "prep brief", or invokes "/p-meeting-prep". Suitable for early-morning scheduled runs.
argument-hint: "[--date YYYY-MM-DD] [--lang ja|en] [--dry-run] [--no-open]"
compatibility: Requires gws CLI and gh CLI. Slack MCP and Fireflies MCP recommended (skill degrades gracefully without them).
metadata:
  author: jackchuka
  scope: personal
  layer: workflow
  confirms:
    - write files to local disk
  skillctx:
    version: "0.1.0"
---

# Meeting Prep

<!-- skillctx:begin -->
## Setup
Locate this skill's directory (the folder containing this SKILL.md), then run the
resolver script from there:

```bash
python <skill-dir>/scripts/skillctx-resolve.py resolve p-meeting-prep
```

The resolver outputs each binding as `key: value` (one per line). Substitute each `{binding_key}` placeholder below with the resolved value.

If any values are missing or the user requests changes, use:
```bash
python <skill-dir>/scripts/skillctx-resolve.py set p-meeting-prep <key> <value>
```
<!-- skillctx:end -->

Generate per-meeting prep briefs for today's calendar (one markdown file per meeting + an index), writing to `{output_dir}/YYYY-MM-DD/`.

## When to Use

- User says "meeting prep", "prep my meetings", "prep brief"
- User invokes `/p-meeting-prep`
- A scheduled cron / launchd job triggers `/p-meeting-prep` (typically early morning)

## Prerequisites

- `gws` CLI installed and authenticated (Google Calendar)
- `gh` CLI authenticated (`gh auth status`)
- Slack MCP connected (optional — skip gracefully if unavailable)
- Fireflies MCP connected (optional — skip gracefully if unavailable)
- skillctx config initialized for `p-meeting-prep`

## Arguments

- `--date YYYY-MM-DD` — Target date. Default: today.
- `--lang ja|en` — Output language. Default: `{default_lang}`.
- `--dry-run` — Print briefs to stdout instead of writing files.
- `--no-open` — Skip auto-opening the index after generation.

## Workflow

(filled in by later tasks)

### Phase 1: Initialize

1. Parse arguments:
   - `--date YYYY-MM-DD` (default: today, local time)
   - `--lang ja|en` (default: `{default_lang}`)
   - `--dry-run` (default: false)
   - `--no-open` (default: false)
2. Compute:
   - `TARGET_DATE`: the date to process, `YYYY-MM-DD`
   - `WEEKDAY`: short weekday name (e.g. `Tue`)
   - `OUTPUT_DAY_DIR`: `{output_dir}/{TARGET_DATE}` (expand `~` and env vars)
3. Confirm prerequisites:
   - `gws` is on PATH (`command -v gws`); if missing, fail with a clear error.
   - `gh auth status` succeeds; if not, fail with a clear error.
   - Slack MCP is reachable (one cheap call, e.g. `slack_read_user_profile`); if not, mark Slack as `UNAVAILABLE` and continue.
   - Fireflies MCP is reachable (one cheap call, e.g. `fireflies_get_user`); if not, mark Fireflies as `UNAVAILABLE` and continue.
4. Record availability flags as `SOURCES_AVAILABLE = {calendar: bool, github: bool, slack: bool, fireflies: bool}` for use in Phase 3.

### Phase 2: Calendar fetch + classify

1. Fetch the day's events.
   → See `references/agent-gather-calendar.md`
2. Filter out junk:
   - Declined events (the user's response is `declined`).
   - All-day events.
   - Events with only one attendee = the user (focus blocks, holds).
3. Classify everything else in a single LLM call.
   → See `references/agent-classify-meetings.md`
4. Cluster meetings by `topic_key`. A cluster is any set of 2+ meetings sharing the same `topic_key`. Singletons are clusters of one and need no cross-links.
5. Save the classified list as `MEETINGS = [{event, category, topic_key, cluster_id, …}]` for Phase 3.

### Phase 3: Parallel source fetch

For each meeting, pick the source set from this table:

| Category   | Fireflies | Slack DMs/mentions | GitHub (attendees) | Slack topic search | Web (candidate) |
| ---------- | --------- | ------------------ | ------------------ | ------------------ | --------------- |
| 1:1        | yes       | yes                | yes                | no  | no  |
| team-sync  | yes       | no                 | yes (self)         | yes | no  |
| external   | yes       | yes                | no                 | yes | no  |
| interview  | yes       | no                 | no                 | no  | yes |
| other      | no        | no                 | no                 | no  | no  |

Fan out all required fetches in parallel within a single tool-use batch where possible. Deduplicate by `topic_key`: a Fireflies or Slack topic search keyed off `topic_key` is run once per cluster, not once per meeting.

For each source, follow the corresponding reference:

- Fireflies → `references/agent-gather-fireflies-meeting-context.md`
- Slack → `references/agent-gather-slack-meeting-context.md`
- GitHub → `references/agent-gather-github-attendee-context.md`
- Web (candidate) → `references/agent-gather-web-candidate-context.md`

If a source's `SOURCES_AVAILABLE` flag is false (from Phase 1), skip every call to it and mark the corresponding sections as `_(unavailable)_` later in Phase 4.

Each fetch has a soft budget of 15 seconds; on timeout, treat as unavailable for that meeting.

Save results as `MEETING_CONTEXT[event_id] = {fireflies, slack_attendees, slack_topic, github, web_candidate}`.

### Phase 4: Synthesize briefs

For each meeting in `MEETINGS`:

1. Pick the template by `category`:
   - `1:1` → `references/template-1on1.md`
   - `team-sync` → `references/template-team-sync.md`
   - `external` → `references/template-external.md`
   - `interview` → `references/template-interview.md`
   - `other` → `references/template-other.md`
2. Render the template using `MEETING_CONTEXT[event_id]`, in language `{lang}`.
3. If the meeting belongs to a cluster of size ≥ 2, add the `Related today:` line referencing the sibling filenames computed in Phase 5.
4. Empty data sections render as `_(no relevant context found)_` rather than being omitted, so the user can tell the skill looked.

Store the rendered markdown per event as `BRIEFS[event_id]`.

### Phase 5: Write files

1. Compute `OUTPUT_DAY_DIR` = `{output_dir}/<TARGET_DATE>` (expand `~`).
2. If `OUTPUT_DAY_DIR` already exists:
   - Remove any existing `<OUTPUT_DAY_DIR>.bak/`.
   - `mv` the current `OUTPUT_DAY_DIR` to `<OUTPUT_DAY_DIR>.bak/`.
3. Create `OUTPUT_DAY_DIR`.
4. Compute filenames in chronological order:
   - `NN` = zero-padded sequence starting at 01 (the index uses `00`).
   - `HHMM` = local start time, 24-hour, no colon.
   - `<slug>` = ASCII-folded, lowercase, hyphenated title; collapse runs of non-`[a-z0-9]` to a single `-`; trim to 40 chars; strip leading/trailing `-`.
   - Final name: `NN-HHMM-<slug>.md`.
5. Write `00-index.md` first:

```markdown
# Meeting prep — <TARGET_DATE> (<WEEKDAY>)
<N> meetings · <K> categories · <C> clusters

## Today
- HH:MM **<title>** `[category]` → [NN-HHMM-slug.md](NN-HHMM-slug.md)<` · cluster: <topic_key>` if cluster size ≥ 2>
... (one bullet per meeting, chronological)

## Clusters
- `<topic_key>` — <count> meetings (HH:MM, HH:MM, ...)
... (only clusters with size ≥ 2)
```

If `N == 0`, the index body is `No meetings today.` and no per-meeting files are written.

6. Write one file per meeting using `BRIEFS[event_id]`.
7. Print the absolute path to `00-index.md` and a one-line summary (`N meetings · K categories · C clusters`).
8. On macOS (`uname -s` = `Darwin`), unless `--no-open` or `--dry-run`, run `open "<00-index.md>"`.
9. If `--dry-run`, do NOT touch the filesystem at all. Instead, print to stdout: the index body, then each brief separated by `---`.

## Error Handling

| Error                                       | Action                                                                                  |
| ------------------------------------------- | --------------------------------------------------------------------------------------- |
| `gws` not installed or not authenticated    | Abort with clear error message. The calendar is required.                               |
| `gh` not authenticated                      | Mark GitHub `UNAVAILABLE`; continue. Add a warning to the top of `00-index.md`.         |
| Slack MCP unavailable                       | Mark Slack `UNAVAILABLE`; continue. Slack sections render as `_(unavailable)_`.         |
| Fireflies MCP unavailable                   | Mark Fireflies `UNAVAILABLE`; continue. Fireflies sections render as `_(unavailable)_`. |
| Classification LLM call fails / bad JSON    | Treat every meeting as `other`. Add a warning to the top of `00-index.md`.              |
| Per-meeting source fetch timeout (15s)      | Section renders as `_(unavailable)_`. No retry within this run.                         |
| `OUTPUT_DAY_DIR` exists from a prior run    | Rename to `<dir>.bak/` (replacing any prior backup) before writing.                     |
| Calendar empty for the target date          | Write `00-index.md` with body `No meetings today.` Exit 0.                              |
| `--dry-run` set                             | Print to stdout only. Do not touch the filesystem. Do not call `open`.                  |
| Filename slug collision (rare)              | Append `-2`, `-3`, … to the slug until unique within the day's directory.               |

## Scheduling

This skill is user-triggered. Two recipes for running it automatically each morning are documented in `references/cron-recipes.md`. Whichever you pick, ensure the scheduled environment inherits credentials for `gh`, `gws`, the Slack MCP server, and the Fireflies MCP server.
