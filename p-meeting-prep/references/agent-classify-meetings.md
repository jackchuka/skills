# Agent: Classify Meetings

Classify all kept events in a single batched call. Do not call once per meeting.

## Input

A JSON array, one object per event:

```json
{
  "id": "evt_xxx",
  "title": "1:1 Alice / Jack",
  "start": "2026-05-19T09:00:00+09:00",
  "end":   "2026-05-19T09:30:00+09:00",
  "attendees": [
    {"email": "jack@tailor.tech", "self": true},
    {"email": "alice@tailor.tech", "self": false}
  ],
  "description": "...",
  "recurrence": "weekly",
  "organizer": "jack@tailor.tech"
}
```

## Output (per event)

```json
{
  "id": "evt_xxx",
  "category": "1:1",
  "topic_key": "alice-1on1",
  "confidence": "high",
  "reason": "Recurring weekly meeting with one other internal attendee"
}
```

## Rules

- `category` ∈ { `1:1`, `team-sync`, `external`, `interview`, `other` }.
- `topic_key` is a short kebab-case slug (max 4 hyphen-separated words). Always emit one — clustering depends on it.
- For 1:1s with a recurring counterpart, prefer the person's first name in the slug (`alice-1on1`).
- For externals, prefer the company name (`acme-onboarding`, `acme-implementation-review` collapse to `acme-onboarding` if clearly part of the same engagement).
- For team-syncs, prefer the team name from the title.
- `confidence` ∈ { `high`, `med`, `low` }.

## Bias

If `{interview_calendar_id}` is set and the event's calendar id matches, the model should bias strongly toward `interview` even without keywords in the title.

## Failure mode

If the model fails to produce valid JSON, fall back to category `other` for all events and surface a warning in the index file.
