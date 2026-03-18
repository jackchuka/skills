# Agent: Gather Slack Activity (Previous Business Day)

Search for user's own messages from the previous business day:

```
slack_search_public_and_private(query="from:me", sort="timestamp", sort_dir="desc", limit=50)
```

**Filtering rules:**
- Only keep messages with timestamps from the previous business day (convert Unix timestamps)
- Remove noise: messages under 10 characters, messages that are just links, emoji-only messages
- Remove messages from `{channel_name}` (standup channel itself)
- Group by channel name
- Extract the topic/substance of each message (do NOT include full message text)

**Context variables:**
- `PREV_DATE` — previous business day in `YYYY-MM-DD` format (computed in Phase 1)
