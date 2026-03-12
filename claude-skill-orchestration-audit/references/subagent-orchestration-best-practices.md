# Subagent Orchestration in AI Coding Agent Skills

## The Three-Phase Pattern

Every skill with subagents follows this structure:

1. **Setup** — Define shared context (time ranges, IDs, params) passed to all agents
2. **Dispatch** — Launch parallel agents, one per independent data source/task
3. **Aggregate** — Merge results, deduplicate, produce single output

## Dispatch Modes

### Parallel (no dependencies between agents)

Best for: data gathering from independent sources, search across platforms, per-repo operations.

```
Launch N agents in parallel — one per source.
Each receives shared context, returns structured results.
If a source is unavailable, skip gracefully.
```

### Sequential Phases with Internal Parallelism

Best for: workflows where phase B needs phase A's output.

```
Phase 1 (parallel): Gather from 4 sources → wait for all
Phase 2 (parallel): Query 2 sources using Phase 1 results → wait for all
Phase 3 (sequential): Aggregate → single output
```

## Six Rules (from battle-tested skills)

| Rule | Why |
|------|-----|
| Share context upfront | Pass time ranges, IDs, keywords to all agents at dispatch |
| Collect independently, aggregate later | Agents don't need each other's results |
| Deduplicate at merge time | Results overlap; filter after all complete |
| Skip unavailable sources | If an MCP server isn't installed, continue without it |
| Cache across invocations | Same check in multiple agents → run once, reuse |
| One consolidated output | N agents → 1 journal / report / message |

## Cross-Provider Support

| Provider | Mechanism | Parallel? |
|----------|-----------|-----------|
| Claude Code | `Agent` tool | Yes (multiple calls in one message) |
| OpenAI Codex | `spawn_agent` / `wait` / `close_agent` (requires `collab = true`) | Yes |
| Cursor | Built-in (up to 8 subagents, automatic) | Yes, but not skill-driven |
| Cline / Windsurf / Aider | No native subagent tool | No (single-agent only) |

## Writing Portable Skills

For maximum portability, describe **what** to do, not **how** to dispatch:

```markdown
## Step N: Gather Data (parallelize if possible)
Collect from these independent sources:
- Source A: ...
- Source B: ...

If your platform supports parallel subagents, dispatch one per source.
Otherwise, query each sequentially.
```

Claude Code uses `Agent`, Codex uses `spawn_agent`, single-agent platforms run sequentially. Skill logic stays the same — only throughput changes.

## SKILL.md Template

```markdown
---
name: my-skill
description: Use when [triggering conditions only, no workflow summary]
---

# Skill Name

## Overview
One sentence.

## Step 1: Setup
Define shared context:
- `PARAM_A`: ...
- `PARAM_B`: ...

## Step 2: Dispatch Agents
Launch N Agent tool calls in parallel — one per [source/repo/keyword].
Each agent receives: PARAM_A, PARAM_B.
Each agent returns: structured results.
If a source is unavailable, skip gracefully.

## Step 3: Aggregate
After ALL agents return:
1. Merge results
2. Deduplicate
3. Synthesize
4. Produce single output
```

## Latent Parallelism in Sequential Skills

Many skills are written as linear step-by-step workflows but contain phases where independent sub-tasks could run in parallel. Recognizing these patterns is as important as checking existing orchestration.

### Common Patterns

| Pattern | Example | How to exploit |
|---------|---------|---------------|
| **Per-item scaffolding** | "scaffold a doc for each actor/flow/feature" | Fan out one agent per item after shared setup completes |
| **Per-item implementation** | "write one file per resolver/page/command" | Each file is independent — dispatch per item |
| **Multi-source research** | "search Odoo, Oracle, SAP" | One agent per source, aggregate findings |
| **Independent tracks** | "implement commands" then "implement queries" | Commands and queries touch different files — run in parallel after shared dependency (fixtures, generated types) |

### Enabling Parallelism in Sequential Skills

To convert a sequential phase into a parallel one:

1. **Identify the sync barrier** — the last step that must complete before fan-out (e.g., code generation, user approval, scaffold creation)
2. **Define the intermediate artifact** — a structured output from the barrier step that each parallel agent consumes (e.g., list of items to process, generated types)
3. **Add "parallelize if possible"** — annotate the fan-out phase so orchestrators know to dispatch multiple agents
4. **Guard shared files** — if parallel agents might touch the same file (index.ts, layout, config), either write shared files before fan-out or designate one agent to own them

### When NOT to Parallelize

- **Human-in-the-loop phases** — if the phase requires user decisions between items, keep it sequential
- **Trivial items** — if each item takes <5 seconds, orchestration overhead exceeds the gain
- **Tight coupling** — if items share mutable state or write to the same files, parallelism causes conflicts
- **Small N** — if there are always 1-2 items, fan-out adds complexity for negligible benefit

## Anti-Patterns

- Agents depending on each other's output (breaks parallelism)
- Summarizing workflow in the `description` field (Claude follows description instead of reading skill body)
- Passing entire result sets between agents (use filesystem or TodoWrite as shared state)
- Deduplicating during collection instead of at merge time
- Writing sequential loops where items are clearly independent (missed parallelism)
- Fan-out without a defined sync barrier (agents start before shared context is ready)
- Parallel agents writing to the same file without guardrails (merge conflicts)
