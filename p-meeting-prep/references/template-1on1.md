# Template: 1:1 Brief

## Header (always)

```markdown
### HH:MM–HH:MM <Meeting title>  `[1:1]`
Attendees: <names>
Meet: <link or "—">
Related today: <links to sibling cluster briefs, if any>
```

If there are no sibling briefs, omit the `Related today:` line entirely.

## Body sections (in this order)

### Since last time

- 1–2 lines summarizing the previous 1:1 (from Fireflies `overview`).
- Up to 3 bullets of still-open action items the user owes the counterpart.
- If no prior recording: `_(no prior recording found)_`.
- If Fireflies unavailable: `_(unavailable)_`.

### Their recent activity

- Up to 3 bullets from `github.recent_prs / recent_issues / recent_reviews`, formatted as `[title](url) — repo · state`.
- Up to 2 notable Slack threads from `slack_attendees.recent_threads`, formatted as `[snippet…](permalink)`.
- If both sources empty: `_(no notable activity in last 7 days)_`.
- If GitHub unavailable: GitHub bullets become `_(unavailable)_`.
- If Slack unavailable: Slack bullets become `_(unavailable)_`.

### What to raise

- 2–3 bullets synthesized from: still-open action items + recent Slack threads + their recent activity.
- Each bullet should be a concrete topic, not a question. Use `{lang}` (ja or en) for phrasing.

### Open questions for them

- Each entry from `slack_attendees.open_questions_awaiting_user` becomes a bullet: `<question> ([source](permalink))`.
- If empty: `_(no pending questions)_`.
