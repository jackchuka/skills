# agent-gather-slack-report

Call `slack_read_user_profile()` (no args) to get the current user's Slack ID.

## Search for Your Messages

Search for messages you sent during the report date range:

```
slack_search_public_and_private(query="from:me", sort="timestamp", sort_dir="desc", limit=50)
```

Filter results by timestamp to match the report date range. If `on:` date filtering is needed, add date qualifiers to the query: `"from:me after:{start_date} before:{end_date}"`.

## Categorize Conversations

Group messages by channel and summarize what you communicated:

| Keep                         | Drop                               |
| ---------------------------- | ---------------------------------- |
| Substantive discussions      | Bot/automated messages             |
| Decisions made               | Simple reactions or emoji-only     |
| Questions asked/answered     | "ok", "thanks", "sounds good"      |
| Status updates shared        | Duplicate cross-posts              |
| Announcements or FYIs posted | Thread noise (repeated follow-ups) |

## Summarize by Channel

Group messages into channel-level summaries. Use channel names as context:

| Channel Messages                                 | Summary                               |
| ------------------------------------------------ | ------------------------------------- |
| #eng: "deployed v2", "fixed the flaky test"      | Shared deployment update and test fix |
| #project-x: "design looks good", "let's ship it" | Approved design and greenlit shipping |
| #team: "OOO tomorrow", "standup notes..."        | Shared availability and standup notes |
