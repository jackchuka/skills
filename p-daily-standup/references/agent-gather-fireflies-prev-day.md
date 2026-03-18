# Agent: Gather Meeting Summaries (Previous Business Day)

Fetch transcripts filtered by the previous business day date range:

```
fireflies_get_transcripts — filter by date range (previous business day)
```

For each meeting found, parallelize if possible — each call is independent:

```
fireflies_get_summary — get action items, key topics, overview
```

**Extraction:**
- Meeting title
- Key topics discussed
- Action items assigned to the user

**Error handling:**
- If Fireflies MCP is unavailable, skip gracefully and note "Meeting summaries unavailable"

**Context variables:**
- `PREV_DATE` — previous business day in `YYYY-MM-DD` format (computed in Phase 1)
