---
name: gws-meeting-scheduler
description: Schedule meetings between people using the `gws` CLI (Google Calendar). Use when the user wants to find a meeting time, schedule a meeting, check availability, or book time with someone. Triggers on requests like "schedule a meeting with X", "find time with Y", "book a 1:1", "when can I meet with Z", "set up a sync".
compatibility: Requires gws CLI
metadata:
  author: jackchuka
  scope: generic
  confirms:
    - create calendar event
---

# Meeting Scheduler

Find mutual availability and create Google Calendar events using the `gws` CLI.

## Prerequisites

- `gws` CLI installed and authenticated

## Workflow

### 1. Resolve attendee email

If the user provides a name but no email, search past calendar events:

```bash
gws calendar events list --params '{"calendarId":"primary","q":"<name>","maxResults":10}'
```

Look at the `attendees` array in results to find the matching email. If multiple matches, ask the user to confirm.

### 2. Detect timezones

Detect each person's timezone by querying **their own calendar** directly. When you query a person's calendar via their email as `calendarId`, the API returns `start.dateTime` with that person's local UTC offset — this is the most reliable signal.

```bash
gws calendar events list --params '{"calendarId":"<user-email>","maxResults":10}'
gws calendar events list --params '{"calendarId":"<attendee-email>","maxResults":10}'
```

For each person:
- Look at `start.dateTime` on non-all-day events (skip events with only `start.date`)
- Extract the UTC offset (e.g., `-08:00`, `+09:00`) — this reflects their calendar's timezone
- Tally the most frequent offset to determine their timezone
- Cross-reference with the `start.timeZone` field on events matching that offset to get the IANA name (e.g., `-08:00` → `America/Los_Angeles`)

**Important:** Do NOT rely on `start.timeZone` alone — it often reflects the *organizer's* or *attendee's* timezone rather than the calendar owner's. The `dateTime` offset from the person's own calendar is the source of truth.

If no timezone can be determined for either person, ask the user.

### 3. Determine date range

Ask the user for a preferred date range, or default to the next 5 business days.

### 4. Check free/busy

Query both calendars together. The query range must cover work hours in **both** timezones:

```bash
gws calendar freebusy query --json '{
  "timeMin": "<start-RFC3339>",
  "timeMax": "<end-RFC3339>",
  "items": [{"id": "<user-email>"}, {"id": "<attendee-email>"}]
}'
```


### 5. Compute overlapping free slots

- Convert all busy times from UTC to **each person's timezone**
- Define work hours per person: 9:00-18:00 in their respective timezone
- Find the **overlap** of both people's work-hour windows, then subtract combined busy blocks
- Filter to slots >= requested meeting duration
- **Double-check every slot against BOTH calendars before presenting** — do not skip the user's own busy times
- Present slots as a table showing times in **both** timezones:

```
Day       | User (JST)    | Attendee (PST) | Duration
Thu Feb 26 | 15:00 - 16:00 | 22:00 - 23:00  | 1h
```

If work-hour overlap is very limited (e.g., < 1 hour), note this and suggest the user consider extending hours.

### 6. Confirm and create the event

Once the user picks a slot, duration, and title:

```bash
gws calendar +insert \
  --summary "<title>" \
  --start "<start-RFC3339>" --end "<end-RFC3339>" \
  --attendee "<user-email>" --attendee "<attendee-email>"
```

For Google Meet links or other advanced options, use the raw API instead:

```bash
gws calendar events insert --params '{"calendarId":"primary","conferenceDataVersion":1,"sendUpdates":"all"}' \
  --json '{
    "summary": "<title>",
    "start": {"dateTime": "<start-RFC3339>"},
    "end": {"dateTime": "<end-RFC3339>"},
    "attendees": [{"email": "<user-email>"}, {"email": "<attendee-email>"}],
    "conferenceData": {"createRequest": {"requestId": "<unique-id>", "conferenceSolutionKey": {"type": "hangoutsMeet"}}}
  }'
```

Key notes:

- `--attendee` — repeat for each attendee, **always include the user themselves**
- `conferenceDataVersion=1` param required when adding Meet links
- `sendUpdates=all` — notify attendees via email

### 7. Confirm to user

Show: title, date/time (in both timezones if cross-timezone), attendees, and Meet link.

## Important Notes

- Always include the user as an attendee, not just as the calendar owner
- `gws` uses `--params` for query/path parameters and `--json` for request bodies
- Use `--format json` (or omit, as JSON is default) for reliable parsing
- RFC3339 times must include timezone offset (e.g., `+09:00` for JST)
- The freebusy API returns busy times in UTC — convert carefully
- When computing free slots, verify against **both** calendars before presenting
- Use `gws calendar +insert` helper for simple events; use `gws calendar events insert` raw API for advanced features (Meet links, recurrence, etc.)
