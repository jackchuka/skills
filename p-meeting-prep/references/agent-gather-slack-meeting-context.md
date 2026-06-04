# Agent: Gather Slack Context per Meeting

For each meeting that uses Slack (1:1, external), gather two kinds of context.

## Per-attendee DM / mention context (1:1, external)

For each non-self attendee:

1. Find their Slack user id by email (`slack_search_users` or equivalent).
2. Pull recent DMs (`slack_read_dm`) — last 7 days, max 30 messages.
3. Pull mentions of the user in shared channels (`slack_search_messages` with `from:@them mentions:@me` or equivalent) — last 7 days, max 20 messages.

## Topic-keyword search (team-sync, external)

Run `slack_search_messages` with derived keywords:

- For `team-sync`: tokens from `topic_key` (e.g. `infra-migration` → `"infra migration"`).
- For `external`: the company name plus tokens from `topic_key`.

Take last 7 days, max 20 messages per query. Deduplicate per `topic_key` (run once per cluster).

## Extract

- `recent_threads` — list of `{channel, permalink, snippet, ts}`.
- `open_questions_awaiting_user` — messages where someone explicitly asked the user something and the user has not replied (best effort).

## Error handling

- If Slack MCP is unavailable, return `{status: "unavailable"}`.
- If an attendee has no Slack profile, skip them silently.
