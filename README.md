# Skills

A collection of [Skills](https://agentskills.io) - jackchuka's personal library of agent workflows.

## Installation

To install skills:

```sh
npx skills add jackchuka/skills
```

## Skills

<!-- SKILLS_START -->
| Skill | Description |
|-------|-------------|
| [claude-permissions-audit](claude-permissions-audit/) |  Review and reorganize Claude Code permission settings across all config files (global settings.json, project settings.local.json, dotfiles copies). Identifies redundancy, misplaced permissions, and lack of read/write organization. Produces a clean layout where global settings are the source of truth and project-local files only contain project-specific overrides. Use this skill whenever the user mentions reviewing permissions, cleaning up settings, auditing allowed tools, reorganizing settings.json, or asking "what permissions do I have". Also use when adding new MCP servers or tools and wanting to decide what to pre-allow. Triggers: "review permissions", "audit settings", "clean up settings.json", "permissions audit", "/permissions-audit". |
| [claude-skill-prereq-audit](claude-skill-prereq-audit/) |  Scan skills for prerequisite tools, MCP servers, and auth requirements, then check if everything is installed and authenticated. Offers to fix issues. Use when setting up a new machine, after installing skills, or to verify your environment. Triggers: "check prerequisites", "skill prereqs", "are my tools installed", "verify skill dependencies", "/claude-skill-prereq-audit". |
| [claude-skill-spec-audit](claude-skill-spec-audit/) |  Audit skill SKILL.md files for compliance with the agentskills.io specification. Checks frontmatter fields (name, description, compatibility, metadata, argument-hint) and metadata sub-fields (author, scope, confirms). Use when adding new skills, reviewing skill quality, or ensuring all skills follow the spec. Triggers: "audit skills", "check skill spec", "skill compliance", "are my skills up to spec", "/claude-skill-spec-audit". |
| [dev-cli-consistency-audit](dev-cli-consistency-audit/) |  Reviews a CLI tool's command interface for consistency in argument naming, flag conventions, help text, and README alignment. Use when building CLI tools or before releasing CLI updates. Triggers: "review CLI arguments", "align CLI conventions", "CLI consistency check", "make sure commands are aligned", "review command interface". |
| [dev-code-quality](dev-code-quality/) |  Systematic codebase quality scan for identifying duplication, redundancy, and improvement opportunities. Use when reviewing a repo's architecture, finding refactoring targets, or assessing code health. Triggers: "scan the repo", "find code duplication", "suggest improvements", "code quality review", "is there redundant code", "refactoring plan", "architecture review". |
| [dev-new-tool](dev-new-tool/) | End-to-end workflow for taking a new tool idea from research to working MVP. Use when the user has an idea for a CLI tool, library, or small project and wants to go from concept to initial implementation. Triggers on I have an idea for a tool, build a new CLI, create a new project, kickoff new tool, I want to build, let's build a new, 新しいツールを作りたい, CLIを作る. |
| [gh-dep-pr-triage](gh-dep-pr-triage/) | Triage and fix dependency update PRs (Renovate, Dependabot, etc.). Use when the user wants to review dependency PRs, check which are mergeable, fix failing CI on dependency updates, or clean up a backlog of automated dependency PRs. Also triggers when the user mentions renovate PRs, dependabot PRs, dependency updates, dep PRs. |
| [gh-oss-release-prep](gh-oss-release-prep/) |  Systematic OSS release preparation checklist. Use when preparing a repository for open-source publishing, making a project public, or ensuring a repo meets OSS standards. Triggers: "prepare for OSS", "ready to publish", "make this public", "OSS checklist", "scan repo for publish", "open source this", "/oss-release-prep" |
| [gh-oss-release](gh-oss-release/) |  Create GitHub releases across multiple OSS repositories. Checks release status via `gh oss-watch releases`, analyzes unreleased commits to recommend semver bumps, confirms with user, then creates releases. Triggers: "create releases", "release my packages", "check for releases", "oss releases", "gh oss-watch releases", "/oss-release", "release status", "bump versions" |
| [git-conventional-commit](git-conventional-commit/) | Create git commits following the Conventional Commits v1.0.0 specification (conventionalcommits.org). Use when the user asks to commit changes, says /conventional-commit, or wants a well-structured commit message. Triggers on requests like commit this, commit my changes, create a commit, or any git commit workflow. Analyzes staged/unstaged changes and produces compliant commit messages with proper type, scope, description, body, and footers. |
| [gws-meeting-scheduler](gws-meeting-scheduler/) | Schedule meetings between people using the `gws` CLI (Google Calendar). Use when the user wants to find a meeting time, schedule a meeting, check availability, or book time with someone. Triggers on requests like schedule a meeting with X, find time with Y, book a 1:1, when can I meet with Z, set up a sync. |
| [project-namer](project-namer/) | Use when naming a project, repository, tool, or product and wanting a memorable, unique name |
| [restaurant-search](restaurant-search/) | Search for Japanese restaurants using the `hpp` CLI (HotPepper Gourmet API). Use when the user wants to find a restaurant, plan a dinner, search for izakayas, or book a group meal in Japan. Triggers on requests like find a restaurant near Shibuya, search for izakayas in 新宿, restaurant for 10 people in 浜松町, dinner spot near Tokyo station. |
| [software-design](software-design/) | Opinionated guide to software design principles and architectural patterns. Use when reviewing code design, planning feature architecture, asking is this the right design?, how should I structure this?, or requesting design philosophy guidance. Triggers on questions about SOLID, DRY, KISS, YAGNI, Clean Architecture, DDD, hexagonal architecture, composition vs inheritance, coupling, cohesion, or any software design trade-off discussion. |

<!-- SKILLS_END -->

## Development

This README is generated from the SKILLS.md files in each skill directory. To update it, run:

```sh
./generate-readme.sh
```

## License

All skills are licensed under the [MIT License](LICENSE).
