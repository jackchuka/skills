<div align="center">

# skills

**Agent Skills for GitHub chores, code review, and the daily work loop.**

32 [Agent Skills](https://agentskills.io) that turn repeatable workflows into one prompt,<br>
installable into Claude Code, Copilot, Cursor, Codex, and other agents that read `SKILL.md`.

[![Test](https://github.com/jackchuka/skills/actions/workflows/test.yml/badge.svg)](https://github.com/jackchuka/skills/actions/workflows/test.yml)
[![Validate Skills](https://github.com/jackchuka/skills/actions/workflows/validate-skills.yml/badge.svg)](https://github.com/jackchuka/skills/actions/workflows/validate-skills.yml)
[![Release](https://img.shields.io/github/v/release/jackchuka/skills?sort=semver)](https://github.com/jackchuka/skills/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Installation](#installation) · [Quick Start](#quick-start) · [Skills](#skills) · [Conventions](#conventions) · [Contributing](CONTRIBUTING.md)

</div>

---

Many engineering chores follow the same steps every time: triage a backlog of dependency PRs, cut releases across a dozen repos, check a repo before making it public, write a standup from yesterday's activity. Explaining those steps to an agent again in every session is slow, and the result varies from run to run.

Each folder here is a self-contained skill: a `SKILL.md` with the procedure, the tools it needs, and the points where it must stop and ask before acting. Some skills also ship helper scripts. Install the ones you want, and the agent loads a skill when your request matches its description.

## Features

- **Spec-compliant** — every `SKILL.md` follows the [agentskills.io specification](https://agentskills.io/specification) and is checked in CI with `gh skill publish --dry-run`
- **Works across agents** — install with `gh skill` or `npx skills` into Claude Code, GitHub Copilot, Cursor, Codex, Gemini CLI, and more
- **Explicit prerequisites** — the `compatibility` field states the CLIs and MCP servers each skill needs (`gh`, `gws`, Slack MCP, ...)
- **Confirmation points** — `metadata.confirms` lists the side effects a skill must confirm before acting, such as creating a release or sending a message
- **Tested helpers** — scripts that ship with a skill (for example `gh-org-chart`'s `collect.sh` and `render.py`) have pytest suites and ruff linting
- **Personal settings kept out of the skill** — `p-*` skills read values like your name or Slack channel from `~/.config/skillctx/config.json` instead of hard-coding them

## Installation

With the [GitHub CLI](https://cli.github.com) (v2.90.0 or later, `gh skill` is in preview):

```bash
gh skill install jackchuka/skills                       # pick skills interactively
gh skill install jackchuka/skills gh-dep-pr-triage      # one skill
gh skill install jackchuka/skills --all --agent claude-code --scope user
```

With the [`skills`](https://www.npmjs.com/package/skills) CLI:

```bash
npx skills add jackchuka/skills                         # pick skills interactively
npx skills add jackchuka/skills --skill gh-dep-pr-triage
npx skills add jackchuka/skills --list                  # list without installing
```

Or copy a skill folder by hand into your agent's skills directory (for Claude Code, `~/.claude/skills/<name>/`).

## Quick Start

1. **See what is available.** Run `gh skill install` without a skill name in a non-interactive shell to print the catalog:

   ```console
   $ gh skill install jackchuka/skills | cut -c1-80
   Using ref v0.6.1 (2a18ef5c)
   Note: found 32 skill(s) at the repository root
   [root] claude-permissions-audit	Review and reorganize Claude Code permission setti
   [root] claude-skill-orchestration-audit	Audit skills for agentic orchestration qu
   ...
   ```

2. **Install** the skills you want (see [Installation](#installation)).

3. **Check prerequisites.** Install `claude-skill-prereq-audit` and ask the agent to "check prerequisites". It reads each installed skill's `compatibility` field and reports missing CLIs, MCP servers, or authentication.

4. **Ask in plain language.** The agent picks the skill from its description, or you can call it by name:

   ```text
   > triage the open renovate PRs in this repo
   > /gh-oss-release-prep
   > find time with alice next week for a 1:1
   ```

## Skills

The table below is generated from each skill's frontmatter by `./generate-readme.sh`.

<!-- SKILLS_START -->
| Skill | Description |
|-------|-------------|
| [claude-permissions-audit](claude-permissions-audit/) |  Review and reorganize Claude Code permission settings across all config files (global settings.json, project settings.local.json, dotfiles copies). Identifies redundancy, misplaced permissions, and lack of read/write organization. Produces a clean layout where global settings are the source of truth and project-local files only contain project-specific overrides. Use this skill whenever the user mentions reviewing permissions, cleaning up settings, auditing allowed tools, reorganizing settings.json, or asking "what permissions do I have". Also use when adding new MCP servers or tools and wanting to decide what to pre-allow. Triggers: "review permissions", "audit settings", "clean up settings.json", "permissions audit", "/permissions-audit". |
| [claude-skill-orchestration-audit](claude-skill-orchestration-audit/) |  Audit skills for agentic orchestration quality. Checks subagent dispatch patterns, parallelism opportunities, anti-patterns, and alignment with the three-phase pattern (setup → dispatch → aggregate). Use when reviewing skill quality, saying "audit orchestration", "check my skills for parallelism", "skill orchestration review", or "/claude-skill-orchestration-audit". |
| [claude-skill-prereq-audit](claude-skill-prereq-audit/) |  Scan skills for prerequisite tools, MCP servers, and auth requirements, then check if everything is installed and authenticated. Offers to fix issues. Use when setting up a new machine, after installing skills, or to verify your environment. Triggers: "check prerequisites", "skill prereqs", "are my tools installed", "verify skill dependencies", "/claude-skill-prereq-audit". |
| [claude-skill-spec-audit](claude-skill-spec-audit/) |  Audit skill SKILL.md files for compliance with the agentskills.io specification and house conventions. Checks frontmatter fields (name, description, compatibility, metadata, argument-hint), metadata sub-fields (author, scope, layer, confirms), and layer/suffix consistency. Use when adding new skills, reviewing skill quality, or ensuring all skills follow the spec. Triggers: "audit skills", "check skill spec", "skill compliance", "are my skills up to spec", "/claude-skill-spec-audit". |
| [dev-cli-consistency-audit](dev-cli-consistency-audit/) |  Reviews a CLI tool's command interface for consistency in argument naming, flag conventions, help text, and README alignment. Use when building CLI tools or before releasing CLI updates. Triggers: "review CLI arguments", "align CLI conventions", "CLI consistency check", "make sure commands are aligned", "review command interface". |
| [dev-code-quality](dev-code-quality/) |  Systematic codebase quality scan for identifying duplication, redundancy, and improvement opportunities. Use when reviewing a repo's architecture, finding refactoring targets, or assessing code health. Triggers: "scan the repo", "find code duplication", "suggest improvements", "code quality review", "is there redundant code", "refactoring plan", "architecture review". |
| [dev-new-tool](dev-new-tool/) | End-to-end workflow for taking a new tool idea from research to working MVP. Use when the user has an idea for a CLI tool, library, or small project and wants to go from concept to initial implementation. Triggers on I have an idea for a tool, build a new CLI, create a new project, kickoff new tool, I want to build, let's build a new, 新しいツールを作りたい, CLIを作る. |
| [dev-software-design](dev-software-design/) | Opinionated guide to software design principles and architectural patterns. Use when reviewing code design, planning feature architecture, asking is this the right design?, how should I structure this?, or requesting design philosophy guidance. Triggers on questions about SOLID, DRY, KISS, YAGNI, Clean Architecture, DDD, hexagonal architecture, composition vs inheritance, coupling, cohesion, or any software design trade-off discussion. |
| [gh-dep-pr-triage](gh-dep-pr-triage/) | Triage and fix dependency update PRs (Renovate, Dependabot, etc.). Use when the user wants to review dependency PRs, check which are mergeable, fix failing CI on dependency updates, or clean up a backlog of automated dependency PRs. Also triggers when the user mentions renovate PRs, dependabot PRs, dependency updates, dep PRs. |
| [gh-issue-report](gh-issue-report/) |  Investigate and file bug reports on GitHub repositories. Searches existing issues to avoid duplicates, checks contributing guides and issue templates, optionally confirms the bug in source code, and files a well-structured issue. Works on both local and remote repos. Triggers: "file a bug", "report issue", "is there a bug for", "check if reported", "investigate and file", "bug report on", "/gh-issue-report" |
| [gh-org-chart](gh-org-chart/) |  Generate an interactive HTML org explorer from a GitHub organization. Surfaces team hierarchy, members, owned repos, and CODEOWNERS path attributions. Two stages: collect.sh writes a canonical JSON, render.py emits a self-contained HTML file. The JSON is the cache (mtime ≤ 24h skips re-collection) and is hand-editable. Triggers: "org chart", "team chart", "visualize github org", "who owns this repo", "github team hierarchy", "/gh-org-chart" |
| [gh-oss-go-bump](gh-oss-go-bump/) |  Bump Go version across multiple OSS repositories. Use when the user wants to update Go across repos, says "bump go version", "update go", "go version bump", "upgrade go", or mentions updating Go in their projects. Also triggers on "go 1.x", "latest go", "go security update", "/go-bump". |
| [gh-oss-release-prep](gh-oss-release-prep/) |  Systematic OSS release preparation checklist. Use when preparing a repository for open-source publishing, making a project public, or ensuring a repo meets OSS standards. Triggers: "prepare for OSS", "ready to publish", "make this public", "OSS checklist", "scan repo for publish", "open source this", "/oss-release-prep" |
| [gh-oss-release](gh-oss-release/) |  Create GitHub releases across multiple OSS repositories. Checks release status via `gh oss-watch releases`, analyzes unreleased commits to recommend semver bumps, confirms with user, then creates releases. Triggers: "create releases", "release my packages", "check for releases", "oss releases", "gh oss-watch releases", "/oss-release", "release status", "bump versions" |
| [gh-review-triage](gh-review-triage/) |  Triage PR reviews assigned to you and your teams. Produces a single prioritized table using a decision-tree + LLM hybrid approach. Use when the user wants to triage their review queue, prioritize PR reviews, check what PRs need attention, or asks "what should I review next", "review triage", "my review queue", "pending reviews". |
| [git-conventional-commit](git-conventional-commit/) | Create git commits following the Conventional Commits v1.0.0 specification (conventionalcommits.org). Use when the user asks to commit changes, says /conventional-commit, or wants a well-structured commit message. Triggers on requests like commit this, commit my changes, create a commit, or any git commit workflow. Analyzes staged/unstaged changes and produces compliant commit messages with proper type, scope, description, body, and footers. |
| [gws-meeting-scheduler](gws-meeting-scheduler/) | Schedule meetings between people using the `gws` CLI (Google Calendar). Use when the user wants to find a meeting time, schedule a meeting, check availability, or book time with someone. Triggers on requests like schedule a meeting with X, find time with Y, book a 1:1, when can I meet with Z, set up a sync. |
| [p-activity-digest](p-activity-digest/) | Summarize recent communication activity from Slack and meeting recordings. Use when the user wants to know what happened on Slack, review meeting action items, find mentions, or get a communication summary. Triggers on summarize Slack, meeting action items, what was discussed, activity summary, search my mentions, highlight of the day, /activity-digest. |
| [p-blog-post-mining](p-blog-post-mining/) |  Mine development activities for blog-worthy topics and create outlines. Analyzes Claude session history, GitHub commits/PRs, Slack discussions, and Fireflies meeting recordings to find interesting stories. Use when the user wants blog ideas, content inspiration, or asks "what can I write about", "find blog material", "blog ideas from my work", "/blog-post-mining". |
| [p-blog-writer](p-blog-writer/) |  Write blog posts in {user_name}'s voice with theoretical depth and persuasive arguments. Iterative workflow: intake → outline → section-by-section expansion → polish. Adapts to tool announcements, opinion pieces, deep-dives, and tutorials. Use when the user says "/blog-writer", "write a blog post", "draft an article about", "help me write about", or wants to create blog content. |
| [p-clipboard-copy](p-clipboard-copy/) |  Pull copy-worthy fragments out of the ongoing session — commands, code blocks, file paths, URLs, IDs, queries, message drafts, error snippets, diffs — and push them into the macOS clipboard history as separate entries, stripped of markdown fences, shell prompts and line numbers, ordered so the most relevant one is what Cmd+V pastes. Message drafts are copied as rich text so bold and bullet lists survive pasting into Slack. Use when the user says "copy that", "clip this", "copy the command and the path", "put those on my clipboard", "clip the last few things", or "/p-clipboard-copy". |
| [p-daily-reflection](p-daily-reflection/) |  Reflect on past work and iterate to improve. Analyzes Claude sessions, GitHub, Slack, and Fireflies to generate a journal entry with actionable improvements. Updates persistent memory with confirmed learnings. Use when the user says "reflect", "reflection", "what can I improve", "retrospective", "review my work", or "/daily-reflection". |
| [p-daily-report](p-daily-report/) | Use when reviewing what you worked on, creating standups, writing status updates, tracking daily/weekly progress, or asking what did I do today |
| [p-daily-standup](p-daily-standup/) | Aggregate previous business day activity and post standup update to Slack. Use when the user says standup, daily standup, post status, status update, or /daily-standup. |
| [p-ego-search](p-ego-search/) |  Search for mentions of you across Slack, Fireflies, and GitHub. Triggers on "egosearch", "/egosearch", "search for mentions of me", "who's talking about me". |
| [p-md-to-slides](p-md-to-slides/) | Convert a structured Markdown deck source into a styled Google Slides presentation. Use this skill when the user has a slide.md file (or wants to write one) and wants Google Slides output — talks, LT decks, lecture slides, conference presentations, internal explainers. Trigger phrases include md からスライド作って, slide.md を Google Slides にして, 発表資料を Google Slides で, convert this markdown to slides, build a Google Slides deck from this markdown, make slides from md, /md-to-slides, and similar. Also use when the user references a presentation/<date>/slide.md file structure with `## Slide N — title`, `**話すこと:**`, and `**スライド要素:**` sections. |
| [p-meeting-prep](p-meeting-prep/) | Generate per-meeting prep briefs for today's calendar. Use when the user says meeting prep, prep my meetings, prep brief, or invokes /p-meeting-prep. Suitable for early-morning scheduled runs. |
| [p-news-briefing](p-news-briefing/) | Use when the user asks for news, wants a briefing, says /news-briefing, or asks to aggregate recent information on any topic. Triggers on requests like what's happening with AI, get me news on crypto, news briefing on climate. |
| [p-slack-triage](p-slack-triage/) |  Scan Slack for messages needing your attention, walk through them one-by-one, and draft/send replies. Covers DMs, mentions, threads, and channel activity. Use when the user wants to triage Slack, check what needs attention, or draft replies. Triggers on "triage slack", "check slack", "what needs my attention on slack", "slack replies", "review slack messages", "/slack-triage". |
| [p-violentmonkey-userscript-sync](p-violentmonkey-userscript-sync/) |  Edit a Violentmonkey userscript through its cloud sync folder (Dropbox, OneDrive, Google Drive) so the change actually reaches the browser. Use when adding a keybinding, shortcut, or fix to an existing userscript, or when a userscript edit "didn't apply" / "wasn't updated" after syncing. Triggers: "Violentmonkey", "userscript", "user script", "Tampermonkey script in Dropbox", "add a shortcut to my userscript", "ユーザースクリプトに追加", "反映されない". |
| [project-namer](project-namer/) | Use when naming a project, repository, tool, or product and wanting a memorable, unique name |
| [restaurant-search](restaurant-search/) | Search for Japanese restaurants using the `hpp` CLI (HotPepper Gourmet API). Use when the user wants to find a restaurant, plan a dinner, search for izakayas, or book a group meal in Japan. Triggers on requests like find a restaurant near Shibuya, search for izakayas in 新宿, restaurant for 10 people in 浜松町, dinner spot near Tokyo station. |

<!-- SKILLS_END -->

## Conventions

### Name prefixes

| Prefix    | Area                                                 | Example                   |
| --------- | ---------------------------------------------------- | ------------------------- |
| `claude-` | Claude Code configuration and skill auditing         | `claude-skill-spec-audit` |
| `dev-`    | Software design and code quality                     | `dev-code-quality`        |
| `gh-`     | GitHub repos, PRs, issues, releases, and orgs        | `gh-oss-release`          |
| `git-`    | Local git workflow                                   | `git-conventional-commit` |
| `gws-`    | Google Workspace through the `gws` CLI               | `gws-meeting-scheduler`   |
| `p-`      | Personal productivity (Slack, calendar, notes, blog) | `p-daily-standup`         |

Skills without a prefix (`project-namer`, `restaurant-search`) are standalone utilities.

### Frontmatter metadata

Beyond the spec fields (`name`, `description`, `license`, `compatibility`), skills here use these fields:

| Field               | Values                          | Meaning                                                       |
| ------------------- | ------------------------------- | ------------------------------------------------------------- |
| `metadata.scope`    | `generic`, `personal`           | `personal` skills assume your own accounts and settings       |
| `metadata.layer`    | `workflow`, `primitive`, `renderer` | Multi-step procedure, single action, or output formatter  |
| `metadata.confirms` | list                            | Side effects the agent must confirm first (if the skill has any) |
| `argument-hint`     | string                          | Arguments shown when invoking the skill as a slash command    |

### Personal settings (`p-*` skills)

Eight `p-*` skills, such as `p-daily-standup` and `p-blog-writer`, contain placeholders like `{channel_id}` or `{user_name}`. Before running, the skill calls its bundled resolver, which reads `${XDG_CONFIG_HOME:-~/.config}/skillctx/config.json`; missing values are asked for and saved with `set`:

```bash
python <skill-dir>/scripts/skillctx-resolve.py resolve p-daily-standup
python <skill-dir>/scripts/skillctx-resolve.py set p-daily-standup <key> <value>
```

## Development

Requires [`uv`](https://github.com/astral-sh/uv) and `gh` v2.90.0 or later.

```bash
uv sync --group dev          # install ruff and pytest
uv run pytest                # run helper-script tests
uv run ruff check .          # lint
uv run ruff format --check . # format check (same as CI)
gh skill publish --dry-run   # validate every SKILL.md against the spec
./generate-readme.sh         # regenerate the Skills table
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the repository layout and how to add a skill.

## License

[MIT](LICENSE)
