# Template: 1:1 Brief

## Header (always)

```markdown
### HH:MM–HH:MM <Meeting title>  `[1:1]`
Attendees: <names>
Meet: <link or "—">
Related today: <links to sibling cluster briefs, if any>
```

If there are neither cluster siblings nor Pass 2 cross-scan overlaps, omit the `Related today:` line entirely.

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

- 3–5 bullets, ordered by lens priority, each prefixed with a tag (ja shown; en uses `[Decide]` `[Unblock]` `[Follow-up]` `[Long-term]`):
  1. `【判断】` — decisions awaiting the user: open questions, approvals, direction calls. Include enough inline context to decide on the spot.
  2. `【ブロック解除】` — the counterpart is stuck waiting on the user (reviews, access, coordination). Name the concrete unblocking action.
  3. `【フォロー】` — commitments by either side (Fireflies action items, Slack promises) not visibly closed.
  4. `【中長期】` — at most 1 strategic/coaching prompt (growth, project direction, recurring friction worth naming).
- **Hard rule:** every bullet must carry a "so what / why now" clause. A bullet that merely restates an item from "Their recent activity" is disallowed.
- Include a source link per bullet when available. Use `{lang}` (ja or en) for phrasing.

### Open questions for them

- Each entry from `slack_attendees.open_questions_awaiting_user` becomes a bullet: `<question> ([source](permalink))`.
- If empty: `_(no pending questions)_`.
