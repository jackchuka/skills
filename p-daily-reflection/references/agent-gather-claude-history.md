# Agent: Gather Claude Code History

**Context:** This agent receives `REFLECT_START` (YYYY-MM-DD) and `REFLECT_END` (YYYY-MM-DD).

Read `{claude_history_path}` (last ~3000 lines). Each line is JSON with fields: `timestamp`, `project`, `display`, `sessionId`.

1. Convert timestamps (Unix milliseconds) to dates. Filter to entries where the date falls within `REFLECT_START` to `REFLECT_END`.
2. Group entries by `sessionId`. Keep only sessions with 3 or more entries.
3. For each session, extract:
   - **Project path** — parse from the ghq convention: `github.com/{owner}/{repo}`
   - **What was attempted** — summarize the `display` fields into a short description
   - **Skill / slash command invocations** — look for entries starting with `/`. Keep these; they feed Lens 1 (Skill Health).
   - **Errors, corrections, retries** — look for error messages, repeated attempts at the same task, or user corrections ("no, do X instead")
4. **Noise filtering**: Remove single-word entries ("yes", "no", single digits, "ok", "thanks"). Keep slash commands even if they are short.
5. **Output constraint**: Return max 20 observations, each ≤ 2 sentences.
