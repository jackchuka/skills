# Agent: Gather GitHub Activity

**Context:** This agent receives `REFLECT_START` (YYYY-MM-DD), `REFLECT_END` (YYYY-MM-DD).

1. Get the authenticated user: `gh api user --jq '.login'`
2. Query `contributionsCollection` via GraphQL for the reflection period:
   ```
   gh api graphql -f query='
     query($from: DateTime!, $to: DateTime!) {
       viewer {
         contributionsCollection(from: $from, to: $to) {
           totalCommitContributions
           totalPullRequestContributions
           totalPullRequestReviewContributions
           totalIssueContributions
           commitContributionsByRepository { repository { nameWithOwner } contributions { totalCount } }
           pullRequestContributionsByRepository { repository { nameWithOwner } contributions { totalCount } }
         }
       }
     }' -f from="$REFLECT_START" -f to="$REFLECT_END"
   ```
3. For each repository with commits, fetch commit messages:
   ```
   gh api "repos/{owner}/{repo}/commits?author={user}&since={REFLECT_START}T00:00:00Z&until={REFLECT_END}T23:59:59Z" --jq '.[].commit.message'
   ```
4. Extract:
   - **Commit message patterns** — what kinds of work (feat, fix, refactor, docs, etc.)
   - **PR cycle time** — time from open to merge for PRs closed in the period
   - **Review feedback received** — comments on the user's PRs
