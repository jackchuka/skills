# Agent: Gather GitHub Activity (Previous Business Day)

Run these `gh` commands to find activity on the previous business day. These three commands are independent — run them concurrently if possible.

```bash
# PRs authored (opened or merged)
gh search prs --author=@me --created=PREV_DATE..TODAY_DATE --json title,url,state,repository --limit 50

# PRs merged on that day (may have been created earlier)
gh search prs --author=@me --merged=PREV_DATE..TODAY_DATE --json title,url,state,repository --limit 50

# PRs reviewed
gh search prs --reviewed-by=@me --updated=PREV_DATE..TODAY_DATE --json title,url,state,repository --limit 50
```

**Context variables:**
- `PREV_DATE` — previous business day in `YYYY-MM-DD` format (computed in Phase 1)
- `TODAY_DATE` — today's date in `YYYY-MM-DD` format (computed in Phase 1)

**Post-processing:**
- Deduplicate by PR URL
- Group by repository
- For each PR, note: title, repo, state (open/merged/closed)
