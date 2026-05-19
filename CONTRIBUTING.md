# Contributing

## Layout

```
<skill-name>/           ← shipped to users on install
├── SKILL.md            ← required
└── scripts/            ← optional helper scripts

tests/<skill-name>/     ← repo-only, never shipped
├── test_*.py           ← pytest discovers these
├── fixtures/
└── golden/
```

Code that ships lives in `<skill-name>/`. Tests live in `tests/<skill-name>/` so they don't bloat the user's install.

## Prerequisites

- [`uv`](https://github.com/astral-sh/uv) — `brew install uv`
- [`gh`](https://cli.github.com) — for `gh skill publish --dry-run`

Install dev tools once:

```sh
uv sync --group dev
```

## Adding a skill

1. Create `<skill-name>/SKILL.md` with valid frontmatter (`name`, `description`, `license`, etc.).
2. If the skill has executable code, put it under `<skill-name>/scripts/`.
3. If it has tests, add them under `tests/<skill-name>/test_*.py`.
4. Regenerate the README skills table:

   ```sh
   ./generate-readme.sh
   ```

## Running tests

```sh
uv run pytest                       # all tests
uv run pytest tests/gh-org-chart    # one skill
uv run pytest -k test_render        # by name
```

## Lint & format

```sh
uv run ruff check .          # lint
uv run ruff format .         # auto-format
uv run ruff format --check . # CI-equivalent check
```

CI runs the same commands; fix locally before pushing.

## Validating skill spec

```sh
gh skill publish --dry-run
```

Checks every `SKILL.md` against the [agentskills.io](https://agentskills.io) spec.

## License

By contributing, you agree your work is licensed under the MIT License.
