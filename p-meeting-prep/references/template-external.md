# Template: External / Customer Brief

## Header

```markdown
### HH:MM–HH:MM <Meeting title>  `[external]`
Attendees: <names> (<company>)
Meet: <link or "—">
Related today: <cluster siblings, if any>
```

## Body sections

### Who

- Company name (from non-internal attendee email domain).
- Roles per attendee, best effort from prior context. If unknown: `Unknown role`.

### Prior context

- 1–2 line `overview` from the most recent matched Fireflies recording with anyone from this company.
- Up to 3 bullets from `slack_topic.recent_threads` mentioning the company or `topic_key`.
- If neither has results: `_(no prior context found)_`.
- If a source is unavailable: `_(unavailable)_` for that subsection.

### Suggested agenda

- 3–5 bullets synthesized from: event `description` + open action items + recent threads.
- Phrasing in `{lang}`.

### Risk / watch-outs

- Each unresolved action item the user owes them becomes a bullet: `<item> (from <meeting_date>)`.
- If none: `_(no open commitments to flag)_`.
