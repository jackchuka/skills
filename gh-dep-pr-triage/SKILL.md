---
name: gh-dep-pr-triage
description: Triage and fix dependency update PRs (Renovate, Dependabot, etc.). Use when the user wants to review dependency PRs, check which are mergeable, fix failing CI on dependency updates, or clean up a backlog of automated dependency PRs. Also triggers when the user mentions "renovate PRs", "dependabot PRs", "dependency updates", "dep PRs".
argument-hint: "[<owner/repo> | <owner> (org-wide)] [--merge]"
compatibility: Requires gh CLI, git, and access to the internet
metadata:
  author: jackchuka
  scope: generic
  confirms:
    - approve PRs
    - merge PRs
---

# Dependency PR Triage

End-to-end workflow for triaging dependency update PRs: list them, assess merge safety, and fix CI failures — all with maximum parallelism. Do NOT merge PRs unless the user explicitly asks.

## Phase 1: Discovery

List all open dependency update PRs. Detect the bot automatically (Renovate, Dependabot, etc.).

### Single repo

```bash
gh pr list --repo <owner/repo> --search "author:app/renovate OR author:app/dependabot" \
  --json number,title,author,mergeable,mergeStateStatus,statusCheckRollup,labels,updatedAt
```

### Org-wide scan

When the user specifies an org (or says "all my repos"), search across all repos first, filter out archived repos, then fetch detailed status per repo in parallel:

```bash
# Step 1: Discover all open dep PRs across the org (excluding archived repos)
gh search prs --author app/renovate --author app/dependabot --state open --owner <org> \
  --archived=false --json repository,number,title,updatedAt --limit 100

# Step 2: For each unique repo found, fetch detailed PR status in parallel
gh pr list --repo <owner/repo> --search "author:app/renovate OR author:app/dependabot" \
  --json number,title,mergeable,mergeStateStatus,statusCheckRollup
```

Classify each PR into one of these buckets:

| Bucket          | Criteria                                            | Next step                              |
| --------------- | --------------------------------------------------- | -------------------------------------- |
| **CLEAN**       | `mergeStateStatus=CLEAN`, all checks pass           | Investigate for merge safety (Phase 2) |
| **FAILING**     | One or more checks failing                          | Fix CI (Phase 3)                       |
| **CONFLICTING** | `mergeable=CONFLICTING` or `mergeStateStatus=DIRTY` | Resolve conflicts (Phase 3)            |

Present the full table to the user and ask how they'd like to proceed before moving to the next phase. Do not automatically start investigating or fixing.

## Phase 2: Investigate CLEAN PRs

For each CLEAN PR, run investigations in parallel to assess merge safety.

### Group by dependency, not by PR

When the same dependency appears across multiple repos (e.g., oxlint bumped in 3 repos), investigate it once and apply the verdict to all. Dispatch investigation agents by dependency group:

- One agent for a family of related deps (e.g., all oxlint/oxfmt/tsgolint bumps)
- One agent for Go module bumps
- One agent for major version bumps (these need extra scrutiny)

### Per-dependency investigation

1. **Identify the dependency** — what it does in these projects, where it's used
2. **Check the changelog** — web search for release notes between old and new versions
3. **Assess risk:**
   - Patch bump with no code changes → safe
   - Minor bump with additive features only → safe
   - Pre-1.0 minor bumps (e.g., 0.x → 0.y) → check carefully, semver allows breaking changes
   - Major bump or behavior changes → flag for user review
   - Breaking changes documented → flag with details

Report back a structured summary per dependency:

- Dependency name and role in the project(s)
- Version change (from → to)
- Breaking changes or behavior changes (if any)
- Verdict: **safe to merge** or **needs review** with reasoning

After presenting the investigation summary, ask the user if they want to proceed with fixing failing PRs.

## Phase 3: Fix Failing PRs

Only proceed if the user confirms. For each failing PR, fix it in its own git worktree so fixes run in parallel without interfering with each other or the main working directory.

### Common failure patterns

1. **Lint/format failures** — Run the project's lint and format commands. Often the dependency update changes generated files or type signatures that need reformatting.

2. **Lockfile conflicts** — Accept main's lockfile version, then regenerate with the project's package manager.

3. **Merge conflicts** — Merge main into the PR branch, resolve conflicts, then verify all checks pass.

### Fix workflow per PR

```
1. git worktree add <worktree-path> <pr-branch>
2. cd <worktree-path>
3. Merge origin/main if behind
4. Install dependencies
5. Run lint → fix issues
6. Run format → apply fixes
7. Run typecheck → fix type errors
8. Run doc/code generation if applicable
9. Verify all checks pass locally
10. Commit and push
```

Always run **all** project checks before pushing, not just the one that was failing — dependency updates can cause cascading issues.

## Phase 4: Cleanup

After all fixes are pushed and CI is passing, clean up local worktrees and branches created during the process.

```bash
# List worktrees to see what was created
git worktree list

# Remove each worktree
git worktree remove <worktree-path>
# Or if directories were already deleted:
git worktree prune

# Only delete branches that were created by worktree agents during this session
# Track which branches you create and delete only those specific ones
git branch -D <branch-1> <branch-2> ...
```

Always clean up before finishing — worktrees and local branches accumulate fast when fixing many PRs in parallel.

## Phase 5: Merge (only if user explicitly requests)

Only proceed with merging if the user explicitly asks. Never auto-merge.

When merging multiple dependency PRs, each merge can create conflicts in remaining PRs (especially in lockfiles and generated files).

### Merge strategy

**Parallel across repos, sequential within a repo.** PRs in different repos are independent and can be merged simultaneously. PRs in the same repo must be merged one at a time because each merge can dirty the next PR's lockfile.

### Error handling

`gh pr merge` returns exit code 1 on failure, which cancels all parallel tool calls. Always append `|| true` when merging in parallel to prevent one failure from cancelling the rest:

```bash
# DO: merge across repos in parallel with error isolation
gh pr merge 42 --repo owner/repo-a --squash 2>&1 || true
gh pr merge 13 --repo owner/repo-b --squash 2>&1 || true

# DON'T: bare gh pr merge in parallel (one failure cancels all)
gh pr merge 42 --repo owner/repo-a --squash
```

### Ghost errors

`gh pr merge` can return "Pull Request is not mergeable" even when the merge actually succeeded. If a merge reports failure, verify the actual PR state before assuming it failed:

```bash
gh pr view <number> --repo <owner/repo> --json state --jq .state
```

### Merge order

1. **Merge across repos in parallel** — independent repos can't conflict with each other
2. **Within a repo, merge sequentially** — wait for each merge before attempting the next
3. **After each batch, check remaining PRs** — earlier merges create lockfile conflicts in later PRs
4. **Check if the bot auto-rebased** — Dependabot and Renovate often detect conflicts from earlier merges and auto-rebase the remaining PRs. Check PR status before attempting manual conflict resolution.
5. **Re-resolve if needed** — for PRs that become DIRTY after earlier merges:
   - First check if the bot already rebased (wait a moment, then check `mergeStateStatus`)
   - If still DIRTY: fix in a worktree (merge main, regenerate lockfile, push)
   - Wait for CI to pass, then merge

```bash
gh pr merge <number> --repo <owner/repo> --squash 2>&1 || true
```

### Final sweep

After all merges complete, do a final scan for new PRs that appeared during the session. Merging dependency updates can trigger Renovate/Dependabot to open additional PRs (e.g., transitive dependency bumps). Report any new PRs to the user.

```bash
gh search prs --author app/renovate --author app/dependabot --state open --owner <org> \
  --json repository,number,title --limit 100
```

## Key Principles

- **Maximize parallelism** — investigate and fix PRs concurrently using git worktrees; merge across repos in parallel
- **Isolate errors** — use `|| true` on parallel merge commands to prevent one failure from cancelling the rest
- **Verify before assuming failure** — `gh pr merge` can report false errors; always check actual PR state
- **Check bot auto-rebase** — before manually fixing lockfile conflicts, check if Dependabot/Renovate already rebased
- **Verify locally before pushing** — always run the full check suite, not just the failing check
- **Clean up after yourself** — always remove worktrees and local branches when done
- **Report clearly** — give the user a summary table at each phase so they can make informed decisions
- **Never merge without explicit request** — the default workflow stops after CI is green; merging is a separate step only if asked
- **Final sweep** — after merging, check for newly opened PRs triggered by the merges
