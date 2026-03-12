---
name: claude-skill-orchestration-audit
description: >
  Audit skills for agentic orchestration quality. Checks subagent dispatch patterns,
  parallelism opportunities, anti-patterns, and alignment with the three-phase pattern
  (setup → dispatch → aggregate). Use when reviewing skill quality, saying "audit
  orchestration", "check my skills for parallelism", "skill orchestration review",
  or "/claude-skill-orchestration-audit".
argument-hint: "[skill-name ...] [--fix]"
compatibility: Designed for Claude Code
metadata:
  author: jackchuka
  scope: generic
  confirms:
    - save to filesystem
---

# Skill Orchestration Audit

Check skills against orchestration best practices in `references/subagent-orchestration-best-practices.md`.

## Arguments

- **Skill names**: filter to specific skills
- **--fix**: suggest and apply corrections interactively
- **Default**: scan all skills authored by the user (`metadata.author` match)

## Step 1: Setup

1. Read `references/subagent-orchestration-best-practices.md` — defines the rules
2. Read `references/agent-skill-analyzer.md` — defines the per-skill analysis task
3. Glob `~/.claude/skills/*/SKILL.md` to discover skills. If a directory path is provided as argument, glob `<path>/*/SKILL.md` instead
4. Filter to skills where `metadata.author` matches the user (default: `jackchuka`). If skill names provided, filter to those instead
5. Classify each skill into one of these categories:

| Category                 | Audit type              | Signal                                                                |
| ------------------------ | ----------------------- | --------------------------------------------------------------------- |
| Multi-source aggregation | Orchestration quality   | Already dispatches 2+ parallel agents against independent sources     |
| Multi-step workflow      | Latent parallelism scan | Sequential phases where some sub-tasks within a phase are independent |
| Single-source operation  | Skip                    | One tool/API, truly linear flow, no fan-out possible                  |
| Meta/utility             | Skip                    | Routers, reference libraries, formatters                              |

**How to detect latent parallelism in multi-step workflows:**

Look for phases that iterate over N independent items — even if written as sequential steps:

| Pattern | Example | Signal |
|---------|---------|--------|
| Per-item scaffolding | "scaffold X for each actor/flow/feature" | N independent CLI calls |
| Per-item implementation | "write one file per resolver/page/command" | N independent file writes to separate paths |
| Multi-source research | "search Odoo, Oracle, SAP" | N independent web fetches |
| Independent tracks | "implement commands" then "implement queries" | Parallel tracks after a shared dependency |

A skill is "multi-step workflow" (audit it) if any phase has 2+ items that don't depend on each other. If every phase is truly linear with no fan-out, classify as "single-source operation" and skip.

6. Set `SKILLS_TO_AUDIT` = all skills classified as "multi-source aggregation" or "multi-step workflow"

## Step 2: Dispatch Agents (parallelize if possible)

Launch one agent per skill in `SKILLS_TO_AUDIT`. Each agent receives:

- The skill's SKILL.md content
- The skill's `references/` directory listing (if any)
- Its classification from Step 1
- The check rules from `references/agent-skill-analyzer.md`

Each agent returns structured findings per the format in the reference file. If a skill's SKILL.md can't be read, skip gracefully.

## Step 3: Aggregate & Report

After all agents return:

1. Merge findings across all skills
2. Sort by severity: ERROR → WARN → INFO
3. Produce single consolidated report:

```
## Orchestration Audit

### Skills with existing orchestration

| Skill | Category | S1-4 | P1-4 | C1-3 | A1-3 | X1-4 | Issues |
|-------|----------|------|------|------|------|------|--------|

### Skills with latent parallelism opportunities

| Skill | Opportunity | Phase | Benefit | Issues |
|-------|-------------|-------|---------|--------|

### Findings

#### [skill-name]: [issue count] issues
- **[RULE]:[SEVERITY]** — [description]
  - Current: [what the skill does now]
  - Suggested: [what it should do]

### Top N Highest-Impact Improvements
Rank by benefit (high > medium > low) and usage frequency.

### Summary
N skills checked, M have orchestration, P have latent parallelism, X issues found (E errors, W warnings, I info)
```

## Fix (if --fix or user asks)

| Severity | Action                                            |
| -------- | ------------------------------------------------- |
| ERROR    | Show the fix, apply with Edit after user confirms |
| WARN     | Show suggestion, apply only if user agrees        |
| INFO     | Note for awareness, no auto-fix                   |

After fixing, re-run the check and show updated table.
