# Agent: Gather Fireflies Context per Meeting

For each meeting requiring Fireflies context (1:1, team-sync, external, interview), find at most the 2 most recent prior recordings relevant to that meeting.

## Query strategy by category

- **1:1** — `fireflies_search` with the counterpart's email or full name. Take recordings in last 90 days.
- **team-sync** — `fireflies_search` with the meeting title (strip the date if present). Take last 2 recordings.
- **external** — `fireflies_search` with the external company name (derived from non-internal attendee emails). Take last 2 recordings.
- **interview** — `fireflies_search` with the candidate's name (from event title or description). Take last 3 if available.

## For each matched recording

- `fireflies_get_summary` — overview, key topics, action items.
- Extract:
  - `meeting_date`
  - `overview` (≤ 2 sentences)
  - `action_items_for_user` (those assigned to the current user)
  - `unresolved_threads` (action items that have not been closed elsewhere — best effort, can be the same as `action_items_for_user` for v1)

## Topic clustering optimization

If two meetings in `MEETINGS` share the same `topic_key`, run this query once and reuse the result for both. Cache by `topic_key` within the current run.

## Error handling

- If Fireflies MCP is unavailable, return `{status: "unavailable"}` per meeting.
- If a query returns no results, return `{status: "no-prior-recordings"}`.
