---
name: p-activity-digest
description: Summarize recent communication activity from Slack and meeting recordings. Use when the user wants to know what happened on Slack, review meeting action items, find mentions, or get a communication summary. Triggers on "summarize Slack", "meeting action items", "what was discussed", "activity summary", "search my mentions", "highlight of the day", "/activity-digest".
argument-hint: "[time range] [--sources slack|fireflies|all]"
compatibility: Requires Slack MCP server. Fireflies MCP server optional.
metadata:
  author: jackchuka
  scope: personal
  confirms:
    - save to filesystem
---

# Activity Digest

Aggregate and summarize recent communication activity from Slack messages and meeting recordings (Fireflies). Produces a structured summary with action items, mentions, and key decisions.

## When to Use

- User asks for Slack activity summary
- User wants meeting highlights or action items
- User asks "what was discussed" or "what happened on Slack"
- User wants to find messages where they were mentioned
- Producing communication portions of a daily/weekly report

## Prerequisites

- Slack MCP server configured and authenticated
- Fireflies MCP server configured (optional, for meeting transcripts)

## Workflow

### Step 1: Determine Scope

Ask the user if not clear:

- **Time range**: today, yesterday, past N days, specific date
- **Sources**: Slack only, Fireflies only, or both
- **Focus**: all activity, mentions only, action items only, specific channels/topics

**Shared context** (resolved before dispatch):
- `DATE_START`: start date (YYYY-MM-DD)
- `DATE_END`: end date (YYYY-MM-DD)
- `SOURCES`: which sources to query
- `FOCUS`: filter mode

Steps 2 and 3 are independent data sources. Dispatch both concurrently (parallelize if possible). If your platform supports parallel subagents, launch one per source. Otherwise, query each sequentially.

### Step 2: Gather Slack Activity (parallelize if possible)

Use the Slack MCP tools in this order:

1. **Identify user**: Call `slack_read_user_profile()` (no args) to get the current user's ID.
2. Dispatch all Slack searches in parallel.
3. **Search for mentions**: Call `slack_search_public_and_private` with query `"from:me"` and date-scoped query for the target period to find the user's own messages
4. **Search for mentions of user**: Call `slack_search_public_and_private` with the user's name or handle to find where others mentioned them
5. **Channel context** (optional): If a specific channel is requested, use `slack_read_channel` on that channel for the time period

Combine results and deduplicate.

### Step 3: Gather Meeting Activity

If Fireflies is available and in scope:

1. **Search meetings**: Call `fireflies_get_transcripts` with date filters for the target period
2. For each meeting returned, call `fireflies_get_summary` in parallel (parallelize if possible) — each call is independent.
3. **Get summaries**: For each relevant meeting, call `fireflies_get_summary` to retrieve action items, keywords, and overview
4. **Deep dive** (optional): If the user asks about a specific meeting, call `fireflies_get_transcript` for full conversation content

If Fireflies is unavailable, proceed with Slack data only and note the omission in the output.

SYNC: After all data sources return, merge results into a unified collection before synthesis. If a source was unavailable, proceed with available data.

**Deduplicate**: Before synthesis, deduplicate across sources — the same discussion may appear in both Slack threads and Fireflies meeting notes. Use thread timestamps and meeting IDs as primary keys to merge overlapping records.

### Step 4: Synthesize and Format

Produce a structured summary organized by priority:

```markdown
## Activity Digest - [Date Range]

### Action Items

- [action item from meeting or Slack thread]
- [action item with @assignee if identifiable]

### Key Decisions

- [decision made in meeting or Slack discussion]

### Mentions & Requests

- [someone asked/mentioned you about X in #channel]

### Meeting Highlights

- **[Meeting Title]** — [1-2 sentence summary]
  - Key topics: [topic1], [topic2]

### Slack Activity Summary

- Participated in N threads across [channels]
- [Notable thread summary]
```

Adapt the format:

- If only Slack: omit Meeting Highlights section
- If only Fireflies: omit Slack Activity section
- If action-items-only: show only the Action Items section

### Step 5: Output

- If the user specifies a file path, write to that file
- If the user is composing a daily report, provide the content for insertion
- Otherwise, display directly in the conversation

## Tips

- When searching Slack, use date qualifiers in the query: `"after:2026-02-16 before:2026-02-17"`
- For meeting summaries, the `fireflies_get_summary` tool is much faster than `fireflies_get_transcript` — use summary first, transcript only when needed
- If Slack search returns too many results, narrow by channel or conversation type
- Deduplicate between Slack and meeting notes — the same discussion may appear in both

## Examples

**Example 1: Yesterday's activity**

```
User: "summarize my Slack activity yesterday"
Action: Search Slack messages for yesterday, find mentions, format as digest
```

**Example 2: Meeting action items**

```
User: "what are action items from today's meetings?"
Action: Query Fireflies for today, get summaries, extract action items
```

**Example 3: Full digest for daily report**

```
User: "give me activity digest for today to add to my daily report"
Action: Query both Slack and Fireflies, produce combined summary, write to daily report file
```

**Example 4: Specific mention search**

```
User: "search Slack for messages about me this week"
Action: Search with user's name/handle for past 7 days, summarize findings
```
