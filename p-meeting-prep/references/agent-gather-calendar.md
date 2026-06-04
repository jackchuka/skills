# Agent: Gather Calendar Events

Fetch the target day's events from the user's primary calendar (and any explicitly configured shared calendars such as `{interview_calendar_id}` if set).

## Command

```bash
gws calendar agenda --date "$TARGET_DATE"
```

If `gws calendar agenda` does not accept `--date`, fall back to:

```bash
gws calendar agenda --from "$TARGET_DATE" --to "$TARGET_DATE"
```

(check `gws calendar agenda --help` once if neither form works).

## Extract per event

- `event_id`
- `title`
- `start` (local ISO 8601)
- `end` (local ISO 8601)
- `attendees` — list of `{email, name, self (bool), response_status}`
- `description` (may be empty)
- `recurrence` — `weekly | daily | monthly | none`
- `organizer.email`
- `conference_link` (Meet / Zoom URL if present)

## Error handling

- If `gws` fails entirely, abort the skill with an error — the calendar is the one required source.
- If the day has zero events, return an empty list; do not error.
