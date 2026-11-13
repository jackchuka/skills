---
name: gh-oss-release-prep
license: MIT
description: >
  Systematic OSS release preparation checklist. Use when preparing a repository for open-source publishing,
  making a project public, or ensuring a repo meets OSS standards.
  Triggers: "prepare for OSS", "ready to publish", "make this public", "OSS checklist",
  "scan repo for publish", "open source this", "/oss-release-prep"
argument-hint: "[<repo>]"
compatibility: Requires git and language-specific linters
metadata:
  author: jackchuka
  scope: generic
  layer: workflow
---

# OSS Release Preparation

Systematic workflow to prepare a repository for open-source publishing. Covers code quality, licensing, documentation, CI, and release readiness.

## Key Principle: Convention Reuse

Before creating any file from scratch, check the user's sibling repositories for existing conventions. Users maintain consistency across their repos — reuse their LICENSE text, .golangci.yml, .gitignore, .github/workflows, .goreleaser.yaml, etc. from a recent, well-maintained repo.

**How to find conventions:**
1. Look at sibling directories (e.g., `ls ../`) for other repos by the same user
2. Pick a recently-updated repo with similar characteristics (same language, similar type)
3. Copy config files, adapting only what's project-specific (binary name, module path)

## Step 0: Classify the Project

Before starting, determine the project type — this affects which steps apply:

| Type | Has `main.go` / binary output | Needs goreleaser | Needs package registry |
|------|:---:|:---:|:---:|
| **CLI tool / binary** | Yes | Yes | Homebrew tap, etc. |
| **Library / module** | No | No | `go get` / npm / PyPI |
| **Both** (tool + importable pkg) | Yes | Yes | Both |

This classification drives decisions in Steps 3-7. Don't suggest goreleaser for a library. Don't skip install instructions for a binary.

## Step 1: Repository Scan

Scan the repo and a sibling repo (for conventions):

1. Read the project structure (directories, key files)
2. Check for existing README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT
3. Identify the primary language and build system
4. Check for any sensitive files (.env, credentials, API keys, internal URLs)
5. Review .gitignore for completeness
6. **Scan a sibling repo** for: LICENSE, .gitignore, linter config, .github/workflows, .goreleaser.yaml

Report findings as a checklist:

```
Repository Scan:
- [x/!] README.md exists
- [x/!] LICENSE file exists
- [x/!] .gitignore is comprehensive
- [x/!] .golangci.yml / linter config exists
- [x/!] .github/workflows exists (CI)
- [x/!] No sensitive files detected
- [x/!] No hardcoded internal URLs or secrets
- Reference repo for conventions: <sibling-repo-name>
```

## Step 2: License & Dependency Audit

1. Identify the intended license (check sibling repos first, default: MIT)
2. Check all dependencies for license compatibility:
   - Direct dependencies: list each with its license
   - Flag any copyleft (GPL, AGPL) dependencies that conflict with the chosen license
3. If attribution is required, create or update a NOTICES file
4. Copy LICENSE from sibling repo, updating year if needed

## Step 3: README

Aim for a polished, "awesome" README, not just a complete one. Read `references/readme-guide.md` and follow its layout. A README with only plain sections and no visuals does not pass this step.

1. **Hero block** (centered `<div align="center">`):
   - Name, bold one-line promise, one or two lines on how
   - Badges: test workflow, release, language version, license (only ones that resolve)
   - **Demo GIF** for CLI/TUI tools, recorded with vhs from a committed `assets/demo.tape` against offline fake data (never real accounts)
   - Section nav links
2. **Body**: problem paragraph → Features (bold leads) → Installation (`go install`/brew/`gh extension install` for CLIs, `go get` for libraries) → Quick Start with real output → reference tables (flags, output, config) → Limits → Related → License
3. **Accuracy checks**:
   - Every flag and example matches the actual `--help` / API
   - Example output is copied from a real run (of the demo binary if needed)
   - The demo GIF was regenerated after the last output change and visually checked

## Step 4: Code Quality Review

1. **Copy linter config** from sibling repo if missing (.golangci.yml, .eslintrc, etc.)
2. Run linters and **fix all issues** before proceeding:
   - Go: `golangci-lint run ./...` — fix errcheck, unused, etc.
   - Node/TS: check `package.json` scripts for lint commands
3. Ensure public API documentation exists (exported functions/types have comments)
4. Search for and remove TODO/FIXME comments that reference internal context
5. Run tests, verify they pass

## Step 5: CI/CD Setup

Copy CI configuration from sibling repo, adapting project-specific values:

**For all projects:**
- Test + lint workflow (on push/PR)
- `permissions: contents: read` at the top of every read-only workflow (test, lint, license); grant `write` only in release/publish workflows
- `.github/CODEOWNERS` (`* @<owner>`)
- Dependabot or Renovate config for dependency updates (no `reviewers` key in dependabot.yml; CODEOWNERS handles review requests)
- License check workflow (on dependency changes)

**For CLI tools / binaries only:**
- Release workflow with goreleaser (on tag push)
- `.goreleaser.yaml` if missing

**For libraries only:**
- No release workflow needed (tags are sufficient for `go get` / npm)

## Step 6: Agent Skill

Decide whether the project should ship an [Agent Skills](https://agentskills.io) `SKILL.md` so coding agents can use it. Recommend one way and say why.

**Ship a skill when** agents would use the tool and `--help` alone is not enough:
- Using it takes several steps or judgment (which flags, what to rerun, how to read the output)
- The output needs interpretation before acting on it (verdicts, scores, findings)
- It pairs with other tools in a workflow (feeds PRs, issues, or configs onward)

**Skip it when** the tool is a single obvious command, a library whose API docs already cover usage, or something agents would not run.

If shipping one:
1. **Check for an existing copy first.** Search the user's personal skills repo and `~/.claude/skills` for a skill with the tool's name. Keep one source: the tool repo, so the skill versions with the tool. Merge the useful parts of other copies into it, then ask before deleting them.
2. **Make the CLI agent-ready before writing.** It must run without prompts and offer machine-readable output (`--format json`). Fix gaps in the tool, not with workarounds in the skill.
3. **Place it at `skills/<tool-name>/SKILL.md`**, with `name` equal to the tool name so `gh skill install <owner>/<repo> <tool-name>` reads naturally.
4. **Write it from the real CLI**: flags and JSON field names from `--help` and actual output. Cover setup (install, auth scopes), the workflow, how to read results, and the tool's limits. Leave full flag lists to `--help`.
5. **Keep it public-safe**: generic examples (`acme`, `alice`), no references to the user's personal skills or internal tools. Name a capability ("a dependency-PR triage skill") instead.
6. **Add an `## Agent skill` README section** (and nav link) with:
   ```bash
   gh skill install <owner>/<repo> <tool-name>
   # or
   npx skills add <owner>/<repo> --skill <tool-name>
   ```
   plus one or two example prompts.

## Step 7: Release Readiness Checklist

Present the final checklist (items vary by project type):

```
OSS Release Readiness:
- [ ] LICENSE file is correct and complete
- [ ] All dependency licenses are compatible
- [ ] README is comprehensive and accurate (hero block, badges, nav, features, limits)
- [ ] [CLI only] Demo GIF recorded from `assets/demo.tape` with offline fake data
- [ ] No secrets, internal URLs, or sensitive data in code
- [ ] .gitignore covers build artifacts, IDE files, OS files
- [ ] Linter config exists and passes with no errors
- [ ] CI workflows exist (test, lint, license check) with least-privilege `permissions`
- [ ] .github/CODEOWNERS exists; dependabot.yml has no `reviewers`
- [ ] README's required language version matches go.mod / engines
- [ ] Tests pass
- [ ] Agent skill decision made; if shipped, `skills/<tool>/SKILL.md` matches `--help` and the README has an "Agent skill" section
- [ ] Version/tag strategy defined (semver); libraries have at least one semver tag
- [ ] [CLI only] Release automation configured (goreleaser)
- [ ] [CLI only] Homebrew tap / package registry configured
```

For each unchecked item, provide the specific fix needed.

## Step 8: Final Actions

1. If all checks pass, confirm with user before any publishing steps
2. Commit all changes in a single commit (or logical groups)
3. Push and verify CI passes
4. Suggest next steps:
   - **Libraries**: tag a semver release (e.g. `v0.1.0`), verify `go get` / npm install resolves the tag (not a pseudo-version)
   - **CLI tools**: tag release, verify goreleaser produces artifacts, update Homebrew tap

## Common Issues

- **Missing linter config**: Copy from sibling repo — don't create from scratch
- **Missing CI workflows**: Copy from sibling repo — adapt binary name and module path only
- **Goreleaser for a library**: Don't add it. Libraries don't need binary releases.
- **Missing .gitignore entries**: Add OS-specific (`.DS_Store`), IDE-specific (`.vscode/`, `.idea/`), and language-specific entries
- **Internal references**: Search for company-internal URLs, Slack channels, or employee names in code and docs
- **Inconsistent naming**: Ensure the project name is consistent across README, package.json/go.mod, and CLI help text
- **Linter errors on first run**: Fix them immediately — don't ship with lint failures. Common: errcheck (use `_ =` for intentionally ignored errors), unused imports, missing comments on exports.

## Examples

**Example 1: Go CLI tool**

```
User: "prepare this for OSS"
Action:
1. Classify: CLI tool (has main.go)
2. Find sibling repo with .goreleaser.yaml for conventions
3. Scan repo structure, check for sensitive files
4. Copy LICENSE, .gitignore, .golangci.yml from sibling
5. Check go.mod dependencies for license compatibility
6. Write README per readme-guide; build `assets/demo` fake backend, record `assets/demo.tape` with vhs, check the GIF
7. Run golangci-lint, fix all errors
8. Copy .github/workflows (test, license, release) from sibling
9. Copy .goreleaser.yaml from sibling, update binary name
10. Decide on an agent skill; if yes, write `skills/<tool>/SKILL.md` and the README section
11. Present checklist, commit, push
```

**Example 2: Go library**

```
User: "make this repo public"
Action:
1. Classify: library (no main.go, no binary output)
2. Find sibling repo for conventions
3. Scan repo, check for sensitive files
4. Copy LICENSE, .gitignore, .golangci.yml from sibling
5. Check dependency licenses
6. Ensure README has go get install + usage examples
7. Run golangci-lint, fix all errors
8. Copy .github/workflows (test, license only — NO release/goreleaser)
9. Present checklist, commit, push
```

**Example 3: Node.js library**

```
User: "open source this"
Action:
1. Classify: library (no bin in package.json)
2. Find sibling repo for conventions
3. Scan for .env files, hardcoded URLs
4. Copy LICENSE, .gitignore from sibling
5. Check package.json dependencies' licenses
6. Ensure README has npm install + usage + API docs
7. Run configured lint/test scripts, fix issues
8. Copy .github/workflows from sibling (test only)
9. Present checklist, commit, push
```

## Language References

Read the appropriate reference file for templates and conventions before creating config files:

- **README (all projects)**: `references/readme-guide.md` — layout, badges, vhs demo GIF with offline fake data
- **Go**: `references/go-conventions.md` — .golangci.yml, .gitignore, .github/workflows, .goreleaser.yaml, dependabot, errcheck fixes
