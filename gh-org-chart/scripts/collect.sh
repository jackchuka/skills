#!/usr/bin/env bash
# Collect team / member / repo / CODEOWNERS data for a GitHub org and emit JSON.
# Usage: collect.sh <org> [--no-members] [--no-codeowners]
set -euo pipefail

WITH_MEMBERS=1
WITH_CODEOWNERS=1
ORG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-members)    WITH_MEMBERS=0;    shift;;
    --no-codeowners) WITH_CODEOWNERS=0; shift;;
    -h|--help)
      sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    -*) echo "Unknown flag: $1" >&2; exit 1;;
    *)  ORG="$1"; shift;;
  esac
done
[[ -z "$ORG" ]] && { echo "org required" >&2; exit 1; }

COLLECTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

teams_raw=$(gh api --paginate "/orgs/$ORG/teams")
teams=$(echo "$teams_raw" | jq '[.[] | {
  slug, name, description,
  parent: (if .parent then .parent.slug else null end),
  members: [],
  repos: []
}]')

team_count=$(echo "$teams" | jq 'length')
for i in $(seq 0 $((team_count - 1))); do
  slug=$(echo "$teams" | jq -r ".[$i].slug")

  if [[ "$WITH_MEMBERS" == "1" ]]; then
    # Maintainers are fetched separately, then diffed against the full member
    # list to tag each member's role. members: [{login, role}].
    maintainers=$(gh api --paginate "/orgs/$ORG/teams/$slug/members?role=maintainer" | jq '[.[].login]')
    members=$(gh api --paginate "/orgs/$ORG/teams/$slug/members" | jq --argjson mn "$maintainers" '
      [.[] | {
        login: .login,
        role: (if (.login as $l | $mn | index($l)) then "maintainer" else "member" end)
      }]')
    teams=$(echo "$teams" | jq --argjson m "$members" ".[$i].members = \$m")
  fi

  repos=$(gh api --paginate "/orgs/$ORG/teams/$slug/repos" | jq '[.[] | {
    name: .full_name,
    archived: (.archived // false),
    permission: (
      if   .permissions.admin    then "admin"
      elif .permissions.maintain then "maintain"
      elif .permissions.push     then "push"
      elif .permissions.triage   then "triage"
      else "pull" end
    )
  }]')
  teams=$(echo "$teams" | jq --argjson r "$repos" ".[$i].repos = \$r")
done

codeowners_map='{}'
if [[ "$WITH_CODEOWNERS" == "1" ]]; then
  # Owned repos: any repo where some team has admin or maintain
  owned=$(echo "$teams" | jq -r '
    [.[] | .repos[] | select(.permission == "admin" or .permission == "maintain") | .name]
    | unique | .[]')

  while IFS= read -r repo; do
    [[ -z "$repo" ]] && continue
    raw=""
    for p in CODEOWNERS .github/CODEOWNERS docs/CODEOWNERS; do
      if raw=$(gh api -H "Accept: application/vnd.github.v3.raw" "/repos/$repo/contents/$p" 2>/dev/null); then
        break
      fi
      raw=""
    done
    [[ -z "$raw" ]] && continue

    # Parse: emit slug<TAB>pattern lines for @<ORG>/<slug> owners
    pairs=$(printf '%s\n' "$raw" | awk -v org="$ORG" '
      {
        sub(/#.*/, "")
        if (NF < 2) next
        pattern = $1
        for (i = 2; i <= NF; i++) {
          prefix = "@" org "/"
          if (substr($i, 1, length(prefix)) == prefix) {
            print substr($i, length(prefix) + 1) "\t" pattern
          }
        }
      }')

    # Convert to {team_slug: [pattern, ...]}
    attr=$(printf '%s\n' "$pairs" | jq -R -s '
      split("\n")
      | map(select(length > 0) | split("\t") | {slug: .[0], pattern: .[1]})
      | group_by(.slug)
      | map({key: .[0].slug, value: [.[].pattern]})
      | from_entries')

    codeowners_map=$(echo "$codeowners_map" | jq --arg r "$repo" --argjson a "$attr" '. + {($r): $a}')
  done <<< "$owned"
fi

# Merge codeowner_paths into each team's repos entries
teams=$(echo "$teams" | jq --argjson co "$codeowners_map" '
  map(. as $team | .repos = (.repos | map(
    . as $repo |
    if ($co[$repo.name][$team.slug] // null) != null
    then . + {codeowner_paths: $co[$repo.name][$team.slug]}
    else .
    end
  )))')

jq -n --arg org "$ORG" --arg ca "$COLLECTED_AT" --argjson teams "$teams" '{
  org: $org, collected_at: $ca, teams: $teams
}'
