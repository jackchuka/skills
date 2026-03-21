---
name: dev-cli-consistency-audit
description: >
  Reviews a CLI tool's command interface for consistency in argument naming, flag conventions,
  help text, and README alignment. Use when building CLI tools or before releasing CLI updates.
  Triggers: "review CLI arguments", "align CLI conventions", "CLI consistency check",
  "make sure commands are aligned", "review command interface".
argument-hint: "[<command-name>]"
compatibility: NA
metadata:
  author: jackchuka
  scope: generic
---

# CLI Consistency Review

Systematic review of a CLI tool's command interface to ensure consistent naming, conventions, and documentation alignment.

## Workflow

### Step 1: Inventory Commands

1. Run the CLI with `--help` or `-h` to get the top-level command list
2. For each subcommand, run `<cmd> <subcmd> --help` to get its full interface
3. Build an inventory table:

```
| Command       | Positional Args  | Flags              | Output Formats |
|---------------|------------------|--------------------|----------------|
| pull          | owner/repo       | --issues, --prs    | table, json    |
| search        | [query]          | --type, --limit    | fzf            |
| prune         | owner/repo       | --confirm, --dry-run| table         |
```

### Step 2: Convention Analysis

Check for consistency across all commands:

1. **Positional vs Flag arguments**:
   - Is the same concept (e.g., `owner/repo`) passed as positional in some commands and as `--repo` flag in others?
   - Recommendation: Pick one approach and apply everywhere

2. **Flag naming**:
   - Are similar concepts named consistently? (e.g., `--output` vs `--format` vs `-o`)
   - Do boolean flags follow the same pattern? (`--dry-run` vs `--confirm` vs `--yes`)
   - Are shorthand flags (`-f`, `-o`) assigned consistently?

3. **Pluralization**:
   - Subcommand names: singular vs plural (e.g., `list files` vs `list file`)
   - Flag names: `--issue` vs `--issues`

4. **Default behaviors**:
   - Are defaults consistent? (e.g., if one command defaults to `--format=table`, do others?)
   - Are destructive commands safe by default? (require `--confirm` or `--force`)

5. **Error messages**:
   - Do error messages follow a consistent format?
   - Are they actionable (tell the user what to do)?

### Step 3: Documentation Alignment

1. Compare the README documentation with actual `--help` output:
   - Are all commands documented?
   - Do the documented flags match the actual implementation?
   - Are examples up to date and runnable?

2. Check help text quality:
   - Does each command have a one-line description?
   - Are flag descriptions clear and consistent in style?
   - Do examples in `--help` text work?

### Step 4: Report

Present findings:

```
CLI Consistency Review:

Inconsistencies Found:
1. [Issue] — [Commands affected] — [Suggested fix]
2. ...

Documentation Gaps:
1. [What's missing] — [Where]
2. ...

Recommendations:
1. [Convention to adopt] — [Rationale]
2. ...
```

### Step 5: Apply Fixes

For each accepted fix:

1. Update the command implementation (flag names, defaults, etc.)
2. Update help text and descriptions
3. Update README to match
4. Run `--help` again to verify alignment

## Best Practices Reference

- **Positional arguments**: Use for the primary subject (e.g., `owner/repo`). Limit to 1-2 positional args.
- **Flags**: Use for modifiers and options. Always provide `--long-form`; add `-s` shorthand only for frequently used flags.
- **Boolean flags**: Use `--flag` to enable (default off). For "default on" behaviors, use `--no-flag` to disable.
- **Output format**: If supporting multiple formats, use `--format=table|json|yaml` consistently.
- **Destructive operations**: Default to dry-run or require explicit `--confirm`.
- **Verbosity**: Use `--verbose` / `-v` consistently. Consider `--quiet` / `-q` as well.

## Examples

**Example 1: Full CLI review**

```
User: "review our cli arguments and make sure they are aligned"
Action:
1. Run --help for all commands
2. Build inventory table
3. Identify naming inconsistencies
4. Check README alignment
5. Present report with specific fixes
```

**Example 2: Pre-release check**

```
User: "make sure our command implementation and comments are aligned"
Action:
1. Compare help text with actual behavior
2. Verify README examples work
3. Check for undocumented flags
4. Update docs to match implementation
```
