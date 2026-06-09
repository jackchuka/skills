# Agent: Gather GitHub Context per Attendee

For meetings where GitHub is relevant (1:1, team-sync):

## Per-attendee activity (1:1)

1. Map the attendee email to a GitHub handle, in this order:
   1. **Attendee cache** (see `attendee-cache.md`) — on a hit, use it and skip the rest.
   2. **Org-member search by display name** — `gh search users "<display name>"` and/or list org members (`gh api orgs/<org>/members --paginate`) cross-checked with `gh api users/<candidate>` (compare the `name` field). This is the most reliable strategy: handles often differ from email local-parts (e.g. `jane.doe@…` → `janedoe`).
   3. **Email local-part guess** (last resort) — verify with `gh api users/<handle>` AND confirm org membership before accepting; unverified local-part guesses have matched unrelated stale accounts.
   4. Otherwise return `{status: "no-handle"}` for that attendee and cache `github: null`.

   Write any live resolution back to the attendee cache at end of run.
2. Pull last 7 days of activity:

```bash
gh search prs --author "<handle>" --created ">=$SEVEN_DAYS_AGO" --limit 10 --json title,url,state,repository,createdAt
gh search issues --author "<handle>" --created ">=$SEVEN_DAYS_AGO" --limit 10 --json title,url,state,repository,createdAt
gh search prs --reviewed-by "<handle>" --created ">=$SEVEN_DAYS_AGO" --limit 10 --json title,url,state,repository,createdAt
```

3. Take the top 3 most recent items overall.

## Self activity (team-sync, "my updates")

Same queries but with `--author "{github_handle}"`. Take top 5 by recency.

## Extract

- `recent_prs` — list of `{title, url, state, repo, created_at}`
- `recent_issues` — list of `{title, url, state, repo, created_at}`
- `recent_reviews` — list of `{title, url, repo, created_at}`

## Error handling

- If `gh` auth fails, return `{status: "unavailable"}` for all attendees.
- If a specific attendee's handle cannot be resolved, return `{status: "no-handle"}` for that one and keep going.
