# Template: Team Sync Brief

## Header

```markdown
### HH:MM–HH:MM <Meeting title>  `[team-sync]`
Attendees: <names>
Meet: <link or "—">
Related today: <cluster siblings and Pass 2 overlaps, if any; omit when none>
```

## Body sections

### Since last sync

- 1–2 lines summarizing the previous instance (Fireflies `overview`).
- Up to 3 bullets of decisions and action items from `fireflies.action_items_for_user`.
- If no prior recording: `_(no prior recording found)_`.
- If Fireflies unavailable: `_(unavailable)_`.

### My updates

- Up to 5 bullets from `github` (self activity): `[title](url) — repo · state` (PRs first, then issues, then reviews).
- If GitHub unavailable: `_(unavailable)_`.

### Blockers / things to raise

- Up to 3 bullets from `slack_topic.recent_threads` mentioning the topic, prefixed with the same lens tags as the 1:1 template (`【判断】` `【ブロック解除】` `【フォロー】`; en: `[Decide]` `[Unblock]` `[Follow-up]`). `【中長期】` is normally omitted for syncs.
- Every bullet must carry a "so what / why now" clause, not just a thread summary.
- If Slack unavailable: `_(unavailable)_`.
- If no relevant threads: `_(no open team threads on this topic)_`.
