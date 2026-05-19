---
name: gh-org-chart
license: MIT
description: >
  Generate an interactive HTML org explorer from a GitHub organization. Surfaces
  team hierarchy, members, owned repos, and CODEOWNERS path attributions. Two
  stages: collect.sh writes a canonical JSON, render.py emits a self-contained
  HTML file. The JSON is the cache (mtime ≤ 24h skips re-collection) and is
  hand-editable.
  Triggers: "org chart", "team chart", "visualize github org",
  "who owns this repo", "github team hierarchy", "/gh-org-chart"
argument-hint: "<org> [--refresh] [--no-codeowners] [--no-members]"
compatibility: Requires gh CLI authenticated with read:org scope, jq, and python3
metadata:
  author: jackchuka
  scope: generic
  confirms: []
---

# GitHub Org Chart

Produces two artifacts in `${TMPDIR:-/tmp}/gh-org-chart/`:

- `<org>-org.json` — canonical data: teams, members, owned repos, CODEOWNERS paths. Cache + hand-editable source of truth.
- `<org>-org.html` — single self-contained file with a designed tree (left) and detail pane (right). Opens via `file://`, works offline.

Set `OUT_DIR` once at the start of every phase and reuse it:

```bash
OUT_DIR="${TMPDIR:-/tmp}/gh-org-chart"
mkdir -p "$OUT_DIR"
```

## Arguments

- `/gh-org-chart` — prompt for org.
- `/gh-org-chart <org>` — render-if-fresh: if `<org>-org.json` exists and `mtime` is within 24h, re-render from it. Otherwise collect, then render.
- `/gh-org-chart <org> --refresh` — force re-collect.
- `/gh-org-chart <org> --no-codeowners` — skip CODEOWNERS scan (faster on big orgs).
- `/gh-org-chart <org> --no-members` — drop members from collection and output.

## Phase 1: Intake

1. **Resolve org**: if provided as argument, use it. Otherwise ask:
   > Which GitHub org should I chart?

2. **Verify auth**: run `gh auth status`. Confirm `read:org` is in the scopes line. If not, instruct:
   > `gh auth refresh -s read:org`
   then re-run the skill.

## Phase 2: Decide collect vs. reuse

3. Locate `$OUT_DIR/<org>-org.json`.
4. If `--refresh` was passed, or the file does not exist, or its mtime is older than 24h, run collect (Phase 3). Otherwise skip to Phase 4.

   Freshness check:

   ```bash
   JSON="$OUT_DIR/$ORG-org.json"
   if [[ "$REFRESH" == "1" ]] || [[ ! -f "$JSON" ]] || \
      [[ $(($(date +%s) - $(stat -f %m "$JSON" 2>/dev/null || stat -c %Y "$JSON"))) -gt 86400 ]]; then
     NEEDS_COLLECT=1
   fi
   ```

## Phase 3: Collect

5. Run the bundled collect script (handles zsh `noclobber` via `rm -f`):

   ```bash
   rm -f "$OUT_DIR/$ORG-org.json"
   "${CLAUDE_SKILL_DIR:-$HOME/.claude/skills/gh-org-chart}/scripts/collect.sh" \
     "$ORG" $FLAGS > "$OUT_DIR/$ORG-org.json"
   ```

   Where `$FLAGS` is built from `--no-codeowners` and `--no-members` if set. CODEOWNERS scanning is the long pole — expect ~1 API call per owned repo. Big orgs (200+ owned repos with rate limiting): consider `--no-codeowners`.

## Phase 4: Render

6. Run the renderer:

   ```bash
   python3 "${CLAUDE_SKILL_DIR:-$HOME/.claude/skills/gh-org-chart}/scripts/render.py" \
     "$OUT_DIR/$ORG-org.json"
   ```

   This writes `<org>-org.html` next to the JSON (i.e. in `$OUT_DIR`).

7. Open it (macOS):

   ```bash
   open "$OUT_DIR/$ORG-org.html"
   ```

   Other platforms: report the path so the user can open it themselves.

## Phase 5: Report

8. Summarize (set `JSON="$OUT_DIR/$ORG-org.json"`):
   - Teams: `jq '.teams | length' "$JSON"`
   - Owned repos (admin or maintain): `jq '[.teams[].repos[] | select(.permission == "admin" or .permission == "maintain") | .name] | unique | length' "$JSON"`
   - CODEOWNERS path attributions: `jq '[.teams[].repos[].codeowner_paths // [] | length] | add // 0' "$JSON"`
   - Member entries: `jq '[.teams[].members[]] | length' "$JSON"` (omit if `--no-members`).
   - Whether the JSON was freshly collected or reused from cache.

## Notes

- **Hand-editing the JSON**: edits survive across `/gh-org-chart <org>` runs because the freshness check reuses the file. Use `--refresh` when you want collection to overwrite your edits.
- **CODEOWNERS attribution**: only `@<org>/<team-slug>` owners produce attributions. Individual user owners (`@alice`) and external orgs (`@other-org/team-x`) are intentionally ignored — this is a team-ownership view.
- **No reporting lines**: GitHub teams reflect permission grouping, not management hierarchy. Manager → report relationships need a different data source (HRIS).
- **Performance**: CODEOWNERS scan is restricted to owned repos (permission ≥ maintain) to keep API calls bounded.
