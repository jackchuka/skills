# Priority Cascade Reference

First-match decision tree. Evaluate conditions top-to-bottom; first match assigns the tier.

## Thresholds

| Parameter | Default | Description |
|---|---|---|
| fresh_days | 3 | PRs updated within this many days are "fresh" |
| stale_days | 7 | PRs not updated for this many days are "stale" |

## Cascade

| Step | Condition | Tier | Why-Template |
|---|---|---|---|
| 1 | Draft | ⚪ | "Draft — skip unless asked" |
| 2 | CI red (statusCheckRollup has failures) | ⚪ | "CI failing — review after fix" |
| 3 | Re-review: you have a prior review AND author pushed/commented after it | 🔴 | "Author responded, your turn" |
| 4 | Bug/hotfix (label or title prefix) + fresh + you individually assigned | 🔴 | "Fresh bugfix, you're assigned" |
| 5 | Security dependency (security label) + fresh | 🔴 | "Security patch, review soon" |
| 6 | You are the sole individual reviewer + fresh | 🔴 | "You're the only reviewer" |
| 7 | You individually assigned (+ others too) + fresh | 🟡 | "Assigned to you, others can help" |
| 8 | Fresh + team-only request (no individuals named) | 🟡 | "Team request, recently active" |
| 9 | Stale (≥ stale_days since last update) | ⚪ | LLM judges: abandoned vs slow-moving |
| 10 | Others individually assigned, you NOT individually named | 🔵 | "Others are covering this" |
| 11 | Everything else | 🟡 | LLM narrates |

## Within-Tier Sort

Sort by cognitive_load ascending within each tier: quick → moderate → heavy.

## Derived Fields

These fields are computed from raw PR data during the ENRICH phase:

- **is_bot**: author login ends with `[bot]` or matches known bots (renovate, dependabot, github-actions, etc.)
- **has_your_prior_review**: your GitHub login appears in the `reviews[]` array
- **author_responded_after_you**: author's latest push or comment timestamp is after your latest review timestamp
- **days_since_update**: current date minus `updatedAt`
- **sole_reviewer**: you are the only entry in `reviewRequests[]` that is a User (not a Team)
- **other_individual_reviewers**: User entries in `reviewRequests[]` excluding your login
- **you_individually_assigned**: your login appears as a User in `reviewRequests[]`
- **is_fresh**: days_since_update ≤ fresh_days
- **is_stale**: days_since_update ≥ stale_days
