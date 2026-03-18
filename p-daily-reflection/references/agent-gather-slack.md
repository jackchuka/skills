# Agent: Gather Slack Activity

**Context:** This agent receives `REFLECT_START` (YYYY-MM-DD), `REFLECT_END` (YYYY-MM-DD), and `REFLECT_END_PLUS_1` (YYYY-MM-DD, one day after REFLECT_END).

1. Get the user's Slack ID: call `mcp__plugin_slack_slack__slack_read_user_profile()` (no args) and extract `user_id`.
2. Search sent messages: call `mcp__plugin_slack_slack__slack_search_public_and_private` with query `"from:<@{USER_ID}> after:{REFLECT_START} before:{REFLECT_END_PLUS_1}"` where `REFLECT_END_PLUS_1` is the day after `REFLECT_END`.
3. Search mentions: call `mcp__plugin_slack_slack__slack_search_public_and_private` with query `"<@{USER_ID}> after:{REFLECT_START} before:{REFLECT_END_PLUS_1}"`.
4. Extract:
   - **Decisions made** — messages containing decision language ("let's go with", "decided to", "we'll do")
   - **Questions asked** — messages ending with `?` or containing "how do", "anyone know"
   - **Help given / received** — threads where the user answered someone or someone answered the user
5. **Noise filtering**: Remove bot messages, simple reactions, emoji-only messages, "ok"/"thanks"/"sounds good" one-liners, and thread noise (messages with no substantive content).
