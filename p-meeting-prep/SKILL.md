---
name: p-meeting-prep
license: MIT
description: Generate per-meeting prep briefs for today's calendar. Use when the user says "meeting prep", "prep my meetings", "prep brief", or invokes "/p-meeting-prep". Suitable for early-morning scheduled runs.
argument-hint: "[--date YYYY-MM-DD] [--lang ja|en] [--dry-run] [--no-open] [--non-interactive]"
compatibility: Requires a reachable calendar — either the gws CLI or the Google Calendar MCP. gh CLI, Slack MCP and Fireflies MCP are optional; missing sources degrade to `_(unavailable)_` rather than failing. Scheduled runs must pass `--non-interactive`.
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

None are hard requirements except a reachable calendar. Phase 1 falls back rather than aborting, and records every substitution in `00-index.md`.

| Want | Used for | If missing |
| --- | --- | --- |
| `gws` CLI (authenticated) | Google Calendar | Google Calendar MCP |
| `gh` CLI (`gh auth status`) | attendee activity | GitHub sections render `_(unavailable)_` |
| Slack MCP | DMs, mentions, topic search | Slack sections render `_(unavailable)_` |
| Fireflies MCP | prior recordings | Fireflies sections render `_(unavailable)_` |

## Arguments

- `--date YYYY-MM-DD` — Target date. Default: today.
- `--lang ja|en` — Output language. Default: `{default_lang}`.
- `--dry-run` — Print briefs to stdout instead of writing files.
- `--no-open` — Skip auto-opening the index after generation.
- `--non-interactive` — Never prompt. Fall back silently and render gaps as `_(no relevant context found)_`. **Required for cron / launchd runs**, which have no one to answer.

## Workflow

### Phase 1: Initialize

1. Parse arguments:
   - `--date YYYY-MM-DD` (default: today, local time)
   - `--lang ja|en` (default: `{default_lang}`)
   - `--dry-run` (default: false)
   - `--no-open` (default: false)
   - `--non-interactive` (default: false; treat as true when the invocation came from a scheduler)
2. Compute:
   - `TARGET_DATE`: the date to process, `YYYY-MM-DD`
   - `WEEKDAY`: short weekday name (e.g. `Tue`)
   - `OUTPUT_DAY_DIR`: `{output_dir}/{TARGET_DATE}` (expand `~` and env vars)
3. Resolve prerequisites. **Never abort and never ask — substitute, then report.** Run these probes in one parallel batch.

   | Probe | Missing / failing → fallback | Record as |
   | --- | --- | --- |
   | `command -v gws` | Google Calendar MCP `list_events` (`startTime` / `endTime` / `orderBy: startTime` / `timeZone`). | `calendar: Google Calendar MCP (gws not installed)` |
   | `gh auth status` | none — GitHub sections render `_(unavailable)_` | `github: unavailable` |
   | `slack_read_user_profile` | none — Slack sections render `_(unavailable)_` | `slack: unavailable` |
   | `fireflies_get_user` | none — Fireflies sections render `_(unavailable)_` | `fireflies: unavailable` |

   Abort **only** when `gws` and the Calendar MCP both fail; there is then no calendar at all.

4. Record `SOURCES_AVAILABLE = {calendar, github, slack, fireflies}` for Phase 3, and `FALLBACKS` — the list of "Record as" strings that fired — for Phase 5.

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

### Phase 3: Per-meeting fetch + confirm (interactive)

Read the attendee cache once — `~/.cache/p-meeting-prep/attendees.json` (see `references/attendee-cache.md`) — **before** the loop, and pass relevant entries into every fetch so cached attendees skip live resolution.

Then walk the meetings **one at a time, in chronological order**. Do not fetch the whole day up front: the user sees and confirms each meeting before you move to the next one. `other`-category meetings are skipped entirely — no fetch, no prompt.

For each meeting:

**1. Fetch.** Pick the source set from this table and fan out that meeting's calls in a single parallel tool-use batch.

| Category   | Fireflies | Slack DMs/mentions | GitHub (attendees) | Slack topic search | Web (candidate) |
| ---------- | --------- | ------------------ | ------------------ | ------------------ | --------------- |
| 1:1        | yes       | yes                | yes                | no  | no  |
| team-sync  | yes       | no                 | yes (self)         | yes | no  |
| external   | yes       | yes                | no                 | yes | no  |
| interview  | yes       | no                 | no                 | no  | yes |
| other      | no        | no                 | no                 | no  | no  |

Per source, follow the matching reference:

- Fireflies → `references/agent-gather-fireflies-meeting-context.md`
- Slack → `references/agent-gather-slack-meeting-context.md`
- GitHub → `references/agent-gather-github-attendee-context.md`
- Web (candidate) → `references/agent-gather-web-candidate-context.md`

Skip every call to a source whose `SOURCES_AVAILABLE` flag is false. Soft budget 15 s per source; on timeout treat it as unavailable **for this meeting only**, no retry. Reuse across a cluster: a Fireflies or Slack topic search keyed off `topic_key` runs once per cluster, not once per meeting.

**2. Report.** Print at most 5 lines — one per source — each either a one-line finding or the concrete reason it is empty. Name the gaps; do not let them slide silently into `_(unavailable)_`.

```
HH:MM <title>  [category]
  Fireflies  <one-line finding, or why it is empty>
  GitHub     <one-line finding, or why it is empty>
  Slack      <one-line finding, or why it is empty>
  <other>    <one-line finding, or why it is empty>
```

Never put a real name, handle, email, or identifier into this skill file — the shape above is the contract, the values belong only in the generated brief.

**3. Ask.** One `AskUserQuestion` call (max 4 questions), covering **only gaps the user can actually close**. Skip this step when there are none — never ask a question whose answer changes nothing.

- Closable: things that live outside the wired sources — a link to the counterpart's public profile or résumé, notes from a meeting that was never recorded, a doc or ticket the fetch could not reach, the real subject when the calendar title is opaque, which of several same-name people the attendee is.
- Not closable: a source marked `UNAVAILABLE` back in Phase 1. State it once and move on.
- Every question offers both a paste path and a `なし・このまま進める` path. Never block: "no answer" is a valid answer and means render the gap as `_(no relevant context found)_`.

**4. Fold in** whatever the user pasted. If they gave a URL, fetch it before drafting. Store it as `user_supplied`.

**5. Draft** the brief for this meeting using the Phase 4 rendering rules, and store it as `BRIEFS[event_id]`.

Under `--non-interactive`, run steps 1, 2 and 5 only.

Save results as `MEETING_CONTEXT[event_id] = {fireflies, slack_attendees, slack_topic, github, web_candidate, user_supplied}`.

### Phase 4: Rendering rules + cross-scan

**Pass 1** runs inside the Phase 3 loop (step 5). These are the rules that step follows, for the one meeting being drafted:

1. Pick the template by `category`:
   - `1:1` → `references/template-1on1.md`
   - `team-sync` → `references/template-team-sync.md`
   - `external` → `references/template-external.md`
   - `interview` → `references/template-interview.md`
   - `other` → `references/template-other.md`
2. Render the template using `MEETING_CONTEXT[event_id]`, in language `{lang}`.
3. If the meeting belongs to a cluster of size ≥ 2, add the `Related today:` line referencing the sibling filenames computed in Phase 5.
4. Empty data sections render as `_(no relevant context found)_` rather than being omitted, so the user can tell the skill looked.

5. Anything the user pasted in Phase 3 step 3 outranks a fetched source that contradicts it, and is cited as `（ユーザー提供）` / `(user-supplied)` so the brief stays auditable.

**Pass 2 — cross-scan (after the Phase 3 loop has drafted every brief; no user interaction):**

Filenames are deterministic from Phase 2 data (chronological order + start time + title slug) — compute them before Pass 2 so both cluster links and overlap links can reference sibling files.

1. Detect overlaps across the day's drafts:
   - (a) shared non-self attendees appearing in 2+ meetings;
   - (b) shared salient topics/entities — proper nouns, repo names, project names appearing in 2+ briefs' bodies (e.g. `changelog-management`).
2. For each overlap, inject into the header block of every affected brief:
   `Related today: [<sibling file>](<sibling file>) — <shared attendee or topic, one short clause>`
   Multiple siblings → comma-separated. Merge with any existing cluster-based `Related today:` line rather than duplicating it.
3. `other`-category meetings are excluded from the cross-scan (they have no body and no fetches).
4. Record the overlap list as `OVERLAPS` for the index (Phase 5).

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
   - If ASCII-folding leaves fewer than 4 useful characters (typical for Japanese titles), romanize instead: kanji/kana → romaji words, katakana loanwords → their English source word. Example: `採用：グッズブレストMTG` → `saiyo-goods-brainstorm-mtg`. Same 40-char cap and collision rule.
   - Final name: `NN-HHMM-<slug>.md`.
5. Write `00-index.md` first:

```markdown
# Meeting prep — <TARGET_DATE> (<WEEKDAY>)
<N> meetings · <K> categories · <C> clusters
<`> ` + each FALLBACKS entry, one line — omit the block when FALLBACKS is empty>

## Today
- HH:MM **<title>** `[category]` → [NN-HHMM-slug.md](NN-HHMM-slug.md)<` · cluster: <topic_key>` if cluster size ≥ 2>
... (one bullet per meeting, chronological)

## Clusters
- `<topic_key>` — <count> meetings (HH:MM, HH:MM, ...)
... (only clusters with size ≥ 2)

## Overlaps
- <shared attendee or topic> — <count> meetings (HH:MM, HH:MM, ...)
... (from Pass 2 cross-scan; omit the section when `OVERLAPS` is empty)

## Sources
- Calendar: <✅ + how it was fetched | ❌>
- GitHub / Slack / Fireflies / Web: <✅ | ❌ reason>
- User-supplied: <what the user pasted in Phase 3, per meeting — omit the line when nothing was pasted>
```

If `N == 0`, the index body is `No meetings today.` and no per-meeting files are written.

6. Write one file per meeting using `BRIEFS[event_id]`.
7. Merge any live attendee resolutions from this run back into `~/.cache/p-meeting-prep/attendees.json` (read-modify-write; see `references/attendee-cache.md`).
8. Print the absolute path to `00-index.md` and a one-line summary (`N meetings · K categories · C clusters`).
9. On macOS (`uname -s` = `Darwin`), unless `--no-open` or `--dry-run`, run `open "<00-index.md>"`.
10. If `--dry-run`, do NOT touch the filesystem at all. Instead, print to stdout: the index body, then each brief separated by `---`.

## Error Handling

| Error                                       | Action                                                                                  |
| ------------------------------------------- | --------------------------------------------------------------------------------------- |
| `gws` missing or unauthenticated            | Fall back to Google Calendar MCP; note it in `FALLBACKS`. Abort only if that also fails. |
| `gh` not authenticated                      | Mark GitHub `UNAVAILABLE`; continue. Add a warning to the top of `00-index.md`.         |
| Slack MCP unavailable                       | Mark Slack `UNAVAILABLE`; continue. Slack sections render as `_(unavailable)_`.         |
| Fireflies MCP unavailable                   | Mark Fireflies `UNAVAILABLE`; continue. Fireflies sections render as `_(unavailable)_`. |
| Classification LLM call fails / bad JSON    | Treat every meeting as `other`. Add a warning to the top of `00-index.md`.              |
| Per-meeting source fetch timeout (15s)      | Section renders as `_(unavailable)_`. No retry within this run.                         |
| `OUTPUT_DAY_DIR` exists from a prior run    | Rename to `<dir>.bak/` (replacing any prior backup) before writing.                     |
| Attendee cache missing / corrupt JSON       | Treat as empty cache; resolve live; rewrite the file at end of run.                      |
| Calendar empty for the target date          | Write `00-index.md` with body `No meetings today.` Exit 0.                              |
| `--dry-run` set                             | Print to stdout only. Do not touch the filesystem. Do not call `open`.                  |
| Filename slug collision (rare)              | Append `-2`, `-3`, … to the slug until unique within the day's directory.               |
| User declines to fill a gap (Phase 3)       | Render that section as `_(no relevant context found)_`; move to the next meeting.       |
| User pastes an unreachable URL              | Say so in one line, re-ask once, then continue without it.                              |
| `--non-interactive` set                     | Never call `AskUserQuestion`. Every gap renders as `_(no relevant context found)_`.     |

## Scheduling

Scheduled runs **must** pass `--non-interactive` — nothing is there to answer Phase 3's questions, and an unanswered prompt stalls the whole run.

This skill is user-triggered. Two recipes for running it automatically each morning are documented in `references/cron-recipes.md`. Whichever you pick, ensure the scheduled environment inherits credentials for `gh`, `gws`, the Slack MCP server, and the Fireflies MCP server.
