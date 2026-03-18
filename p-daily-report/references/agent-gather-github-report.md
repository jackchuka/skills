# agent-gather-github-report

Use `gh_user` captured in the Parallel Initialization step (do not re-fetch).

## Global Activity (primary source)

Use GraphQL `contributionsCollection` to find activity across all repos. This is the primary GitHub data source — it covers commits, PRs, reviews, and issues in one query.

```bash
gh api graphql -f query='
query {
  viewer {
    contributionsCollection(from: "{date}T00:00:00Z", to: "{next_date}T00:00:00Z") {
      commitContributionsByRepository {
        repository { nameWithOwner }
        contributions { totalCount }
      }
      pullRequestContributions(first: 20) {
        nodes {
          pullRequest {
            title url state number
            repository { nameWithOwner }
          }
        }
      }
      pullRequestReviewContributions(first: 20) {
        nodes {
          pullRequestReview {
            state
            pullRequest {
              title url number
              repository { nameWithOwner }
            }
          }
        }
      }
      issueContributions(first: 20) {
        nodes {
          issue {
            title url number state
            repository { nameWithOwner }
          }
        }
      }
    }
  }
}'
```

## Per-Repo Commit Messages and PR Supplement (always fetch, parallelize if possible)

The GraphQL query only returns commit counts per repo, not messages. **Always** fetch commit messages for every repo that has commits. Fan out all per-repo `gh api` calls in parallel — do not serialize them in a loop:

```bash
# For each repo with commits — dispatch all concurrently
gh api "repos/{owner}/{repo}/commits?author={gh_user}&since={date}T00:00:00Z&until={next_date}T00:00:00Z" \
  --jq '.[] | "- \(.sha[0:7]) \(.commit.message | split("\n") | .[0])"'
```

**IMPORTANT**: Never output bare "N commits pushed" — it adds no context. Summarize commit messages into short, readable descriptions (e.g., "Added logout button and empty state handling"). Group related commits into one line. If the commit message fetch fails, show "- N commits (details unavailable)".

For the same repo, the PR supplement fetch can run concurrently alongside the commit fetch — no need to wait for commits before fetching PRs:

```bash
# Run concurrently with the commit fetch above, for the same repo
gh pr list -R {owner}/{repo} --author @me --search "updated:{date}" \
  --json number,title,state,url --jq '.[] | "- PR #\(.number) \(.title) [\(.state)]"'
```

Only use the PR supplement if the GraphQL PR data lacks detail for a specific repo.

## Merge and Deduplicate

1. Start with per-repo data from Claude session repos
2. Add global activity items — skip any `owner/repo` already covered by per-repo queries
3. Remaining global items go under **"Other Repositories"** in the output
4. Deduplicate by PR number + repo
