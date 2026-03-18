# Agent: Gather Fireflies Meetings

**Context:** This agent receives `REFLECT_START` (YYYY-MM-DD) and `REFLECT_END` (YYYY-MM-DD).

1. Call `mcp__fireflies__fireflies_get_transcripts` with `fromDate` and `toDate` set to the reflection period.
2. For each meeting returned, call `mcp__fireflies__fireflies_get_summary` to get:
   - Action items assigned to or by the user
   - Decisions made during the meeting
   - Unresolved topics or open questions
3. Extract:
   - **Commitments made** — action items the user owns
   - **Decisions** — choices finalized in the meeting
   - **Topics needing follow-up** — unresolved items, parking-lot topics
