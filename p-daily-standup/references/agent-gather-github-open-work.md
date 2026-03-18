# Agent: Gather Open GitHub Work

Both commands are independent — run them concurrently if possible.

```bash
# Open PRs authored by user
gh search prs --author=@me --state=open --json title,url,repository --limit 20

# PRs where review is requested
gh search prs --review-requested=@me --state=open --json title,url,repository --limit 20
```

**Post-processing:**
- List open PRs authored by user
- List PRs where user's review is requested
- These feed into the やること section of the standup message
