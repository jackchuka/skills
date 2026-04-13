---
name: gh-review-triage
description: >
  Triage PR reviews assigned to you and your teams. Produces a single
  prioritized table using a decision-tree + LLM hybrid approach.
  Use when the user wants to triage their review queue, prioritize PR reviews,
  check what PRs need attention, or asks "what should I review next",
  "review triage", "my review queue", "pending reviews".
argument-hint: "[--no-team] [--limit N]"
compatibility: Requires gh CLI (authenticated), git, internet access
metadata:
  author: jackchuka
  scope: generic
  confirms:
    - none (read-only skill)
---

# PR Review Triage

Triage your PR review queue into a single prioritized table. Combines a mechanical
decision tree (draft status, CI, reviewer assignment, staleness) with LLM judgment
(type classification, cognitive load estimation, priority narration) to produce an
opinionated ordering.

Includes team-assigned reviews by default. Use `--no-team` to show only PRs where
you are individually named as a reviewer.

## Phase 1: Discovery

Fetch all open PRs where review is requested from you (directly or via team membership).

### Identify current user

```bash
gh api user --jq '.login'
```

Store the result as `$ME` for use in all subsequent phases.

### Fetch review-requested PRs

```bash
gh search prs --review-requested=@me --state=open \
  --json repository,title,number,url,author,createdAt,updatedAt,labels,commentsCount,isDraft \
  --limit 100
```

Sort results by `updatedAt` descending (most recently active first).

If `--no-team` is specified, filtering happens in Phase 2 after enrichment — the search API does not distinguish individual vs team assignment.

## Phase 2: Enrich

For each PR from Phase 1, fetch detailed data in parallel (batch 5–10 at a time):

```bash
gh pr view <number> --repo <owner/repo> \
  --json additions,deletions,reviewRequests,reviews,statusCheckRollup,body
```

### Derived fields

Compute the following from raw PR data:

- **is_bot**: `author.login` ends with `[bot]` or matches a known bot (renovate, dependabot, github-actions, etc.)
- **has_your_prior_review**: `$ME` appears in `reviews[].author.login`
- **author_responded_after_you**: find your latest review timestamp, check if `updatedAt` is after it AND latest activity is from the author
- **days_since_update**: today minus `updatedAt` in days
- **sole_reviewer**: `reviewRequests` has exactly one User entry and it is `$ME`
- **other_individual_reviewers**: User entries in `reviewRequests` excluding `$ME`
- **you_individually_assigned**: `$ME` appears as a User (not Team) in `reviewRequests`
- **ci_status**: aggregate `statusCheckRollup` — "pass" if all pass, "fail" if any fail, "pending" if any pending and none fail
- **is_fresh**: `days_since_update` ≤ 3
- **is_stale**: `days_since_update` ≥ 7

### Team filtering

If `--no-team` is specified: drop PRs where `you_individually_assigned` is false. Only PRs where you are explicitly named as a User reviewer survive.

## Phase 3: Classify

Mechanical decision tree. Evaluate conditions top-to-bottom; first match assigns the tier.

### Priority cascade

| Step | Condition | Tier | Why |
|---|---|---|---|
| 1 | `isDraft == true` | ⚪ | "Draft — skip unless asked" |
| 2 | `ci_status == "fail"` | ⚪ | "CI failing — review after fix" |
| 3 | `has_your_prior_review AND author_responded_after_you` | 🔴 | "Author responded, your turn" |
| 4 | type is bug/hotfix (from labels or title) + `is_fresh` + `you_individually_assigned` | 🔴 | "Fresh bugfix, you're assigned" |
| 5 | has `security` label + `is_bot` + `is_fresh` | 🔴 | "Security patch, review soon" |
| 6 | `sole_reviewer` + `is_fresh` | 🔴 | "You're the only reviewer" |
| 7 | `you_individually_assigned` + `is_fresh` | 🟡 | "Assigned to you, others can help" |
| 8 | `is_fresh` + `other_individual_reviewers` is empty (team-only) | 🟡 | "Team request, recently active" |
| 9 | `is_stale` (≥ 7 days since update) | ⚪ | (LLM refines in Phase 4) |
| 10 | `other_individual_reviewers` is non-empty + NOT `you_individually_assigned` | 🔵 | "Others are covering this" |
| 11 | everything else | 🟡 | (LLM narrates in Phase 4) |

See `references/cascade.md` for full field definitions and threshold defaults.

### Quick type detection

Classify PR type mechanically before falling back to LLM:

1. Labels containing "bug", "hotfix", "fix", "Type: Bug" → **bug**
2. Title starts with `fix:`, `fix(`, `hotfix:`, `hotfix(` → **bug**
3. Labels containing "security" → **security** (handled by step 5)
4. Otherwise → not a bug (skip step 4, continue cascade)

## Phase 4: Evaluate (LLM judgment)

Only runs on 🔴 and 🟡 candidates. Skip ⚪ and 🔵 — they are already classified and don't benefit from LLM refinement.

### Input per PR

- **Non-bot PRs**: read PR body (capped at 500 chars from data fetched in Phase 2)
- **Bot PRs**: title + labels only (body is auto-generated boilerplate)

### LLM evaluates per PR

- **Type classification** (fallback chain: labels → title prefix → LLM → "unknown"): bug | hotfix | feat | chore | docs | test
- **Cognitive load** estimation:
  - **quick**: < 100 lines, single file or test-only, docs, config
  - **moderate**: 100–500 lines, 2–5 files, straightforward logic
  - **heavy**: > 500 lines, core logic, multiple components, concurrency
  - Factor in file types — 200 lines of tests are easier than 50 lines of concurrency
- **Why narration**: one sentence combining cascade reason with title/body context
- **Tier override** (rare): promote 🟡 → 🔴 if body says "blocking release", "urgent", "production issue"; demote if exploratory/WIP despite not being marked draft

### Stale PR judgment (step 9)

For PRs that matched the stale rule, the LLM provides nuanced judgment:

- **Abandoned**: no comments, author not active → "Stale — likely abandoned"
- **Slow-moving**: periodic updates, design doc → "Slow-moving, not urgent"
- **Needs attention**: was active, then went silent → "Stale — may need a ping"

This does NOT change the tier (stays ⚪) but improves the "why" column.

## Phase 5: Output

Merge tree tier with LLM refinements. Sort by tier (🔴 → 🟡 → 🔵 → ⚪), then within each tier by cognitive load (quick → moderate → heavy).

### Table format

```
## PR Review Triage ({date}) — {total_count} PRs

| P | PR | Author | Type | Size | Updated | Load | Why |
|---|---|---|---|---|---|---|---|
| 🔴 | [owner/repo#123](https://github.com/owner/repo/pull/123) | alice | fix | +5/-2 | 1h ago | quick | Author responded, your turn |
| 🔴 | [owner/repo#456](https://github.com/owner/repo/pull/456) | renovate | security | +12/-4 | today | quick | Security patch, review soon |
| 🟡 | [owner/repo#789](https://github.com/owner/repo/pull/789) | bob | feat | +200/-30 | 1d ago | moderate | Assigned to you, others can help |
| 🔵 | [owner/repo#101](https://github.com/owner/repo/pull/101) | carol | chore | +8/-0 | today | quick | Others are covering this |
| ⚪ | [owner/repo#201](https://github.com/owner/repo/pull/201) | dave | feat | +300/-40 | 30d ago | heavy | Stale — likely abandoned |
| ⚪ | [owner/repo#301](https://github.com/owner/repo/pull/301) | eve | feat | +1200/-0 | 5d ago | — | Draft |
```

### Footer

```
🔴 {n}  🟡 {n}  🔵 {n}  ⚪ {n} — Review 🔴 first, ~{estimate} estimated
```

Time estimate: quick = 5 min, moderate = 15 min, heavy = 30 min. Sum 🔴 PRs only, round to nearest 5 min.

### Limit

If `--limit N` is specified: show top N rows but still show full tier counts in the footer so the user knows what was omitted.

## Key Principles

- **Freshness over age** — sort by `updatedAt`, not `createdAt`
- **Re-reviews are always top priority** — the author is actively blocked on you
- **Quick wins first within tiers** — 5-line fix takes 2 min, do it before 500-line feature
- **Don't waste tokens on obvious cases** — LLM only refines where judgment adds value
- **Deprioritize when others can cover** — diminishing value when 3 others assigned
- **Read-only** — this skill never modifies PRs, merges, or comments
