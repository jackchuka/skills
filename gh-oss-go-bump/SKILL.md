---
name: gh-oss-go-bump
license: MIT
description: >
  Bump Go version across multiple OSS repositories. Use when the user wants to update Go across repos,
  says "bump go version", "update go", "go version bump", "upgrade go", or mentions updating Go in their
  projects. Also triggers on "go 1.x", "latest go", "go security update", "/go-bump".
argument-hint: "[<go-version>]"
compatibility: Requires gh CLI, gh oss-watch extension, and Go toolchain installed locally
metadata:
  author: jackchuka
  scope: generic
  confirms:
    - create PRs
    - merge PRs
---

# Go Version Bump

Batch workflow for bumping Go versions across multiple OSS repositories. Follows the three-phase pattern: discover and investigate, test locally, then create PRs — with user confirmation gates before every irreversible action.

## Step 1: Discover Go Repos and Latest Go Version

Run these two commands in parallel:

1. **List Go repos:**
   ```bash
   gh oss-watch list
   ```
   Filter to repos where the language column is "Go".

2. **Find latest Go version:**
   Web search for the latest stable Go release. Identify both the latest minor (e.g., 1.26) and latest patch (e.g., 1.26.1).

Present findings to the user:
- Number of Go repos found
- Latest stable Go version
- Key highlights of the new version (security fixes, notable features)

## Step 2: Investigate Each Repo (parallelize if possible)

For each Go repo, dispatch one agent to check:

1. **Current Go version** — fetch `go.mod` via `gh api repos/<owner>/<repo>/contents/go.mod`
2. **CI version strategy** — check if workflows use `go-version-file: go.mod` or hardcoded versions
3. **Open PRs/issues** — check for conflicts with `gh pr list` and `gh issue list`
4. **Test coverage** — check for presence of `_test.go` files
5. **Deprecated patterns** — scan for `io/ioutil`, `reflect.SliceHeader`, or other patterns removed in the target Go version

Each agent returns a structured assessment: repo name, current version, CI strategy, has tests, safe-to-bump verdict, and any concerns.

### Present Investigation Summary

Show a table to the user:

```
| Repo | Current Go | CI Strategy | Has Tests? | Safe? | Notes |
|------|-----------|-------------|-----------|-------|-------|
```

Flag any repos with:
- Large version jumps (2+ minor versions)
- Old dependencies that may need updating
- Hardcoded Go versions in CI (requires extra file changes)
- No tests (higher risk)

**Ask the user to confirm** which repos to proceed with before moving to Step 3.

## Step 3: Test Locally (parallelize if possible)

After user confirms the repo list, dispatch one agent per repo. Each agent:

1. Clones the repo to `/tmp/go-bump/<repo-name>`
2. Edits `go.mod` to set the new Go version
3. Runs `go mod tidy`
4. Runs `go test ./...`
5. Reports: success/failure, any test output, any dependency changes from tidy

Important: these are local-only operations — no branches pushed, no PRs created. This phase is purely for verification.

### Present Test Results

Show a results table:

```
| Repo | Old → New | mod tidy | tests | verdict |
|------|-----------|----------|-------|---------|
```

If any repo fails:
- Show the failure details
- Suggest whether it's fixable (e.g., dependency needs updating) or should be skipped
- Let the user decide

**Ask the user to confirm** before creating PRs. This is the last gate before irreversible actions.

## Step 4: Create PRs (parallelize if possible)

Only after explicit user confirmation. Dispatch one agent per repo using the already-cloned repos in `/tmp/go-bump/`. Each agent:

1. Creates branch `chore/bump-go-<version>` (e.g., `chore/bump-go-1.26.1`)
2. Stages `go.mod` and `go.sum`
3. Commits: `chore: bump Go version from <old> to <new>`
4. Pushes with `-u` flag
5. Creates PR via `gh pr create`:
   - Title: `chore: bump Go version to <new>`
   - Body includes: version change, key improvements (security fixes, performance), and local test results

Each agent returns the PR URL.

### Present PR Summary

Show all created PRs in a table:

```
| Repo | PR URL |
|------|--------|
```

## Step 5: Merge (only if user explicitly requests)

Never auto-merge. Only proceed when the user explicitly asks to merge.

### Check CI First

```bash
gh pr checks <number> --repo <owner>/<repo>
```

Present CI status for all PRs. If any are still running, wait and re-check.

### Merge

After all checks pass and user confirms:

```bash
gh pr merge <number> --repo <owner>/<repo> --squash --delete-branch
```

If `--squash` fails (repo settings), try `--merge`. If that also fails, try `--rebase`.

Present final status table showing all merged PRs.

## Step 6: Cleanup

After all PRs are merged (or the workflow is done):

```bash
rm -rf /tmp/go-bump/
```

## Confirmation Gates

This workflow has three user confirmation points before irreversible actions:

| Gate | Before | Why |
|------|--------|-----|
| **Gate 1** | Local testing (Step 3) | User reviews investigation and chooses which repos to test |
| **Gate 2** | PR creation (Step 4) | User reviews test results before any pushes to remote |
| **Gate 3** | Merging (Step 5) | User reviews CI status before merging to main |

Never skip these gates. If the user says "do everything", still present the investigation summary (Gate 1) — but you may proceed through Gates 2 and 3 without pausing if the user explicitly asked for full automation.

## Key Principles

- **Maximize parallelism** — investigate, test, and create PRs concurrently across repos
- **Test before pushing** — always verify locally with `go mod tidy` and `go test ./...`
- **Confirm before irreversible actions** — PRs and merges require explicit user approval
- **Skip gracefully** — if a repo fails testing, skip it and continue with the rest
- **Clean up** — remove `/tmp/go-bump/` clones when done
- **Detect merge strategy** — repos may require squash, merge, or rebase; try squash first
