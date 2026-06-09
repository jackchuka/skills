# Agent: Gather Calendar Events

Fetch the target day's events from the user's primary calendar (and any explicitly configured shared calendars such as `{interview_calendar_id}` if set).

## Command (verified 2026-06-04)

```bash
TZ_OFF=$(date +%z | sed -E 's/([+-][0-9]{2})([0-9]{2})/\1:\2/')      # e.g. +09:00 (`%:z` is GNU-only; BSD/macOS date emits literal `:z`)
NEXT_DATE=$(date -j -v+1d -f %Y-%m-%d "$TARGET_DATE" +%Y-%m-%d)      # macOS; GNU: date -d "$TARGET_DATE +1 day" +%Y-%m-%d
gws calendar events list --params "{\"calendarId\":\"primary\",\"timeMin\":\"${TARGET_DATE}T00:00:00${TZ_OFF}\",\"timeMax\":\"${NEXT_DATE}T00:00:00${TZ_OFF}\",\"singleEvents\":true,\"orderBy\":\"startTime\"}" --format json
```

## Do NOT use

- `gws calendar agenda` — this subcommand no longer exists.
- `gws calendar +agenda` — helper only returns events from the **current time** (not the full target day) and omits attendees, event IDs, descriptions, and response statuses.

## Extract per event (from `items[]`)

- `event_id` ← `id`
- `title` ← `summary`
- `start` / `end` ← `start.dateTime` / `end.dateTime` (all-day events carry `start.date` instead — filter them out)
- `attendees` ← `attendees[]` as `{email, name: displayName, self, response_status: responseStatus}`
- `description` — may be empty or contain HTML
- `recurrence` ← presence of `recurringEventId` (non-null ⇒ recurring)
- `organizer.email`
- `conference_link` ← `hangoutLink`
- `eventType` — treat `workingLocation`, `outOfOffice`, and `focusTime` like all-day events: filter out.

## Error handling

- If `gws` fails entirely, abort the skill with an error — the calendar is the one required source.
- If the day has zero events, return an empty list; do not error.
