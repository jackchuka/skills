---
name: claude-rc-open
license: MIT
description: >
  Start a new Claude Code session in another local repository that can be driven
  from the phone or claude.ai via Remote Control. It runs as an interactive session
  with permissions bypassed, in the background, so several can run at once, even in
  the same repository. Use when the user says "open <repo>", "start a session in
  <repo>", "<repo> を開いて", "<repo> で作業して", or "/claude-rc-open".
argument-hint: "<repo> [task-name]"
compatibility: >
  macOS; requires ghq, script, and a claude.ai login (Remote Control does not work
  with API-key auth).
metadata:
  author: jackchuka
  scope: generic
  layer: primitive
  confirms:
    - start a background Claude Code session with permissions bypassed
---

# Open a Remote Control session in a repository

Start the session; do not do the task in this session.

1. Resolve the repository under `ghq root`. Given `<owner>/<repo>`, use it as is. Given only `<repo>`, run `ghq list -p | grep "/<repo>$"`; ask if there are several matches or none.
2. Name the session `<repo>`, or `<repo>-<task-name>` when the user gave a task. Keep task names short kebab-case.
3. Run, with `DIR` and `NAME` filled in:

   ```sh
   cd "$DIR" && (tail -f /dev/null | env -u ANTHROPIC_API_KEY -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_CODE_CHILD_SESSION \
     script -q /dev/null claude --dangerously-skip-permissions --remote-control "$NAME" >/dev/null 2>&1 &!)
   ```

   - `script` gives `claude` a pseudo-terminal so it runs without a window; `tail -f /dev/null` keeps its input open.
   - Unsetting `ANTHROPIC_API_KEY` makes it use the claude.ai login, which Remote Control requires. Unsetting the `CLAUDE*` variables stops it from treating itself as a nested session.
   - The new session decides on its own whether to use a worktree.

4. Reply with the session name only. The user opens it from the session list on the phone or at claude.ai/code.

Sessions keep running until stopped. To stop them: `pkill -f 'claude --dangerously-skip-permissions --remote-control'`.
