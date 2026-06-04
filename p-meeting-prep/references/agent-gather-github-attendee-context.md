# Agent: Gather GitHub Context per Attendee

For meetings where GitHub is relevant (1:1, team-sync):

## Per-attendee activity (1:1)

1. Map the attendee email to a GitHub handle. Strategy:
   - Try the local-part of the email (e.g. `alice@example.com` → `alice`) and verify with `gh api users/<handle>`.
   - If that fails, try `gh api search/users?q=<email>+in:email`.
   - If still no handle, skip that attendee.
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
