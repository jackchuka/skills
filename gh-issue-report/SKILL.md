---
name: gh-issue-report
license: MIT
description: >
  Investigate and file bug reports on GitHub repositories. Searches existing issues to avoid duplicates,
  checks contributing guides and issue templates, optionally confirms the bug in source code, and files
  a well-structured issue. Works on both local and remote repos.
  Triggers: "file a bug", "report issue", "is there a bug for", "check if reported",
  "investigate and file", "bug report on", "/gh-issue-report"
argument-hint: "[<owner/repo>] <bug description>"
compatibility: Requires gh CLI authenticated with repo scope
metadata:
  author: jackchuka
  scope: generic
  confirms:
    - create GitHub issues
---

# Issue Report

Investigate a bug, confirm it hasn't been reported, optionally verify in source code, and file a structured issue — all in one workflow.

## Arguments

- `/gh-issue-report` — interactive: asks for repo and bug description
- `/gh-issue-report <owner/repo> <description>` — uses arguments directly

## Phase 1: Intake

1. **Resolve target repo**:
   - If argument includes `owner/repo`, use it.
   - If the current directory is a git repo, offer it as default.
   - Otherwise, ask.

2. **Bug description**: If provided as argument, use it. Otherwise ask:
   > What bug are you seeing? Include steps to reproduce if you have them.

3. **Determine repo locality**:
   - Check if the repo is cloned locally (look for matching remote in `git remote -v` or check common paths).
   - **Local**: use file system tools (Read, Grep, Glob) for code investigation.
   - **Remote-only**: use `gh api` to fetch repo contents for code investigation.

## Phase 2: Search Existing Issues

4. **Search for duplicates** using multiple query strategies in parallel:

   ```bash
   gh issue list -R <repo> --state all --search "<keywords from description>" --limit 20
   ```

   Run 2-3 searches with different keyword combinations extracted from the bug description (e.g., key nouns, component names, error messages). Cast a wide net.

5. **Evaluate matches**:
   - If a clear duplicate exists: show it to the user and ask whether to proceed or comment on the existing issue.
   - If partial matches exist: show them and note the differences.
   - If no matches: continue.

## Phase 3: Check Repo Conventions

6. **Fetch contributing guide and issue templates** in parallel:

   ```bash
   # Contributing guide
   gh api 'repos/<repo>/contents/CONTRIBUTING.md' --jq '.content' | base64 -d

   # Issue templates
   gh api 'repos/<repo>/contents/.github/ISSUE_TEMPLATE' --jq '.[].name'
   ```

   If issue templates exist, fetch the relevant one (usually `bug_report.md` or `bug_report.yml`):

   ```bash
   gh api 'repos/<repo>/contents/.github/ISSUE_TEMPLATE/<template>' --jq '.content' | base64 -d
   ```

7. **Extract conventions**: note title prefix (e.g., `[bug]`), required labels, required sections, and any special instructions from the contributing guide.

## Phase 4: Code Investigation

Adapt investigation depth based on what's achievable. Start lightweight; go deeper only when the lightweight pass yields promising leads.

8. **Lightweight pass** — identify relevant files:

   For **local** repos:
   ```
   Use Grep/Glob to find files matching component names, error messages, or keywords from the bug description.
   ```

   For **remote** repos:
   ```bash
   gh api 'repos/<repo>/git/trees/main?recursive=1' --jq '.tree[].path' | grep -iE '<keywords>'
   ```

   If this yields no useful results (no matching files, or too many to be actionable), skip to Phase 5 and draft the issue without code-level root cause. Note in the issue body that root cause was not confirmed in code.

9. **Deep investigation** — if the lightweight pass found relevant files (< 10 candidates), read them to understand the bug:

   For **local** repos: use Read tool directly.

   For **remote** repos:
   ```bash
   gh api 'repos/<repo>/contents/<path>' --jq '.content' | base64 -d
   ```

   Use subagents for parallel investigation when reading multiple files. Focus on:
   - Where the relevant state is stored (React state, store, DB, etc.)
   - What triggers the bug (lifecycle, navigation, race condition, etc.)
   - Why the current implementation fails

10. **Assess findings**:
    - **Root cause confirmed**: include it in the issue with file paths and line references.
    - **Suspected but unconfirmed**: include as hypothesis, clearly labeled.
    - **Nothing actionable found**: omit code analysis from the issue, describe only the observed behavior.

## Phase 5: Draft Issue

11. **Compose the issue** following the repo's template and conventions:

    Always include:
    - **Title**: follow repo convention (e.g., `[bug] ...`), keep under 80 chars
    - **Description**: clear, concise explanation of the bug
    - **Steps to reproduce**: numbered list
    - **Expected vs actual behaviour**

    Include when available:
    - **Root cause**: with file paths and line references from Phase 4
    - **Suggested fix**: if root cause is clear enough to propose a direction
    - **Environment**: platform, version, relevant config

12. **Infer labels**: fetch repo labels and match against the issue content:

    ```bash
    gh label list -R <repo> --json name,description --jq '.[] | "\(.name)\t\(.description)"'
    ```

    Only use labels that exist on the repo. If the template specifies a label (e.g., `bug`), use it.

13. **Present draft to user**:
    > Here's the issue I'll file. Want me to adjust anything?

    Show the full title, labels, and body. Wait for approval.

## Phase 6: File Issue

14. **Create the issue**:

    ```bash
    gh issue create -R <repo> \
      --title "<title>" \
      --label "<labels>" \
      --body "$(cat <<'EOF'
    <body>
    EOF
    )"
    ```

15. **Report result**:
    ```
    Filed: <issue-url>
    ```
