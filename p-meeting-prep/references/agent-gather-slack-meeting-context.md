# Agent: Gather Slack Context per Meeting

For each meeting that uses Slack (1:1, external), gather two kinds of context.

Slack MCP tool names (verified 2026-06-04): `slack_search_users`, `slack_search_public_and_private`, `slack_read_thread`. Older names `slack_read_dm` and `slack_search_messages` do **not** exist — do not call them.

## Per-attendee DM / mention context (1:1, external)

For each non-self attendee:

1. Resolve their Slack user id: check the attendee cache first (see `attendee-cache.md`). On a miss, `slack_search_users` by email, then write the resolution back to the cache.
2. Search recent messages involving them with `slack_search_public_and_private` — last 7 days, max ~20 results per query. Query patterns that work:
   - `from:@<their-handle> after:<YYYY-MM-DD>`
   - `from:@<their-handle> <user-name> after:<YYYY-MM-DD>`
3. Expand the most notable hits with `slack_read_thread` when a snippet alone is ambiguous.
4. Identify (a) notable threads they are active in, (b) messages where they explicitly asked the user something that appears unanswered.
5. Skip bot noise (reminders, CI notifications, scheduled digests).

## Topic-keyword search (team-sync, external)

Run `slack_search_public_and_private` with derived keywords:

- For `team-sync`: tokens from `topic_key` (e.g. `infra-migration` → `"infra migration" after:<7-days-ago>`).
- For `external`: the company name plus tokens from `topic_key`.

Take last 7 days, max 20 messages per query. Deduplicate per `topic_key` (run once per cluster).

## Extract

- `recent_threads` — list of `{channel, permalink, snippet, ts}`.
- `open_questions_awaiting_user` — messages where someone explicitly asked the user something and the user has not replied (best effort).

## Error handling

- If Slack MCP is unavailable, return `{status: "unavailable"}`.
- If an attendee has no Slack profile, skip them silently (and cache `slack_id: null` — see `attendee-cache.md`).
