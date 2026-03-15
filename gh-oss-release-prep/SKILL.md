---
name: gh-oss-release-prep
description: >
  Systematic OSS release preparation checklist. Use when preparing a repository for open-source publishing,
  making a project public, or ensuring a repo meets OSS standards.
  Triggers: "prepare for OSS", "ready to publish", "make this public", "OSS checklist",
  "scan repo for publish", "open source this", "/oss-release-prep"
compatibility: Requires git and language-specific linters
metadata:
  author: jackchuka
  scope: generic
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

This classification drives decisions in Steps 3-6. Don't suggest goreleaser for a library. Don't skip install instructions for a binary.

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

## Step 3: README Quality Check

Evaluate and improve the README:

1. **Required sections** (create if missing):
   - Project name and tagline (concise, memorable)
   - What it does (1-2 sentences)
   - Installation instructions (adapt based on project type — `go get` for libraries, `go install`/brew for CLIs)
   - Quick start / basic usage
   - License

2. **Recommended sections** (suggest if missing):
   - Features list
   - Configuration options
   - Contributing guidelines (or link to CONTRIBUTING.md)

3. **Quality checks**:
   - Does the README match the actual CLI/API interface?
   - Are code examples up to date and runnable?
   - Is the installation method documented correctly?

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
- Dependabot or Renovate config for dependency updates
- License check workflow (on dependency changes)

**For CLI tools / binaries only:**
- Release workflow with goreleaser (on tag push)
- `.goreleaser.yaml` if missing

**For libraries only:**
- No release workflow needed (tags are sufficient for `go get` / npm)

## Step 6: Release Readiness Checklist

Present the final checklist (items vary by project type):

```
OSS Release Readiness:
- [ ] LICENSE file is correct and complete
- [ ] All dependency licenses are compatible
- [ ] README is comprehensive and accurate
- [ ] No secrets, internal URLs, or sensitive data in code
- [ ] .gitignore covers build artifacts, IDE files, OS files
- [ ] Linter config exists and passes with no errors
- [ ] CI workflows exist (test, lint, license check)
- [ ] Tests pass
- [ ] Version/tag strategy defined (semver)
- [ ] [CLI only] Release automation configured (goreleaser)
- [ ] [CLI only] Homebrew tap / package registry configured
```

For each unchecked item, provide the specific fix needed.

## Step 7: Final Actions

1. If all checks pass, confirm with user before any publishing steps
2. Commit all changes in a single commit (or logical groups)
3. Push and verify CI passes
4. Suggest next steps:
   - **Libraries**: tag release, verify `go get` / npm install works
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
6. Ensure README matches `--help` output
7. Run golangci-lint, fix all errors
8. Copy .github/workflows (test, license, release) from sibling
9. Copy .goreleaser.yaml from sibling, update binary name
10. Present checklist, commit, push
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

- **Go**: `references/go-conventions.md` — .golangci.yml, .gitignore, .github/workflows, .goreleaser.yaml, dependabot, errcheck fixes
