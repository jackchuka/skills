---
name: gh-dep-pr-triage
description: Triage and fix dependency update PRs (Renovate, Dependabot, etc.). Use when the user wants to review dependency PRs, check which are mergeable, fix failing CI on dependency updates, or clean up a backlog of automated dependency PRs. Also triggers when the user mentions "renovate PRs", "dependabot PRs", "dependency updates", "dep PRs".
argument-hint: "[<owner/repo>] [--merge]"
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

```bash
gh pr list --repo <owner/repo> --search "author:app/renovate OR author:app/dependabot" \
  --json number,title,author,mergeable,mergeStateStatus,statusCheckRollup,labels,updatedAt
```

Classify each PR into one of these buckets:

| Bucket          | Criteria                                            | Next step                              |
| --------------- | --------------------------------------------------- | -------------------------------------- |
| **CLEAN**       | `mergeStateStatus=CLEAN`, all checks pass           | Investigate for merge safety (Phase 2) |
| **FAILING**     | One or more checks failing                          | Fix CI (Phase 3)                       |
| **CONFLICTING** | `mergeable=CONFLICTING` or `mergeStateStatus=DIRTY` | Resolve conflicts (Phase 3)            |

Present the full table to the user and ask how they'd like to proceed before moving to the next phase. Do not automatically start investigating or fixing.

## Phase 2: Investigate CLEAN PRs

For each CLEAN PR, run investigations in parallel to assess merge safety:

1. **Read the PR** — `gh pr view <number> --json body,files,commits`
2. **Identify the dependency** — what it does in this project, where it's used
3. **Check the changelog** — web search for release notes between old and new versions
4. **Assess risk:**
   - Patch bump with no code changes → safe
   - Minor bump with additive features only → safe
   - Major bump or behavior changes → flag for user review
   - Breaking changes documented → flag with details

Report back a structured summary per PR:

- Dependency name and role in the project
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

When merging multiple dependency PRs, each merge can create conflicts in remaining PRs (especially in lockfiles and generated files). Strategy:

1. **Merge CLEAN PRs first** — they're already verified and lowest risk
2. **Merge in batches** — after merging a batch, check remaining PRs for new conflicts
3. **Re-resolve conflicts** — for PRs that become DIRTY after earlier merges:
   - Fix in a worktree: merge main, regenerate lockfile, push
   - Wait for CI to pass
   - Then merge

```bash
gh pr review <number> --repo <owner/repo> --approve
gh pr merge <number> --repo <owner/repo> --squash
```

After each merge batch, verify remaining PRs' merge status before attempting the next batch. If a PR goes DIRTY, fix it (Phase 3 workflow) before merging.

## Key Principles

- **Maximize parallelism** — investigate and fix PRs concurrently using git worktrees
- **Verify locally before pushing** — always run the full check suite, not just the failing check
- **Clean up after yourself** — always remove worktrees and local branches when done
- **Report clearly** — give the user a summary table at each phase so they can make informed decisions
- **Never merge without explicit request** — the default workflow stops after CI is green; merging is a separate step only if asked
