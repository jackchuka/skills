# Attendee Cache

Persistent map of attendee email → resolved identities, so GitHub/Slack handle resolution runs once per person, not once per day.

## Location

`~/.cache/p-meeting-prep/attendees.json` — create the directory on first write.

## Schema

```json
{
  "jane.doe@example.com": {
    "github": "janedoe",
    "slack_id": "U01ABCDEF23",
    "display_name": "Jane Doe",
    "last_verified": "2026-06-04"
  }
}
```

## Rules

- **Read at the start of Phase 3.** Every cache hit skips live resolution entirely.
- **Misses are resolved live** (see the GitHub / Slack gather references) and merged back into the file at the end of the run. Read-modify-write; preserve keys you don't recognize.
- **Staleness:** entries with `last_verified` older than 90 days are still used, but re-verify opportunistically (one cheap `gh api users/<handle>` call) and bump the date.
- **Negative caching:** `github: null` / `slack_id: null` are valid values meaning "resolution attempted, nothing found" — they prevent re-probing every run. Null values re-resolve after 30 days.
- **Hand-edits win:** the run never overwrites an existing non-stale value; re-verification only bumps `last_verified`.

## Error handling

- File missing → treat as empty cache; create it at end of run.
- File unreadable / corrupt JSON → treat as empty, resolve live, rewrite the file.
