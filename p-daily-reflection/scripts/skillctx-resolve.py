#!/usr/bin/env python3
"""Resolve and update skillctx skill variables.
Reads/writes ${XDG_CONFIG_HOME:-~/.config}/skillctx/config.json.
Zero external dependencies — uses only Python stdlib."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def get_config_path() -> Path:
    config_dir = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(config_dir) / "skillctx" / "config.json"


def load_config(config_path: Path) -> dict[str, Any] | None:
    if not config_path.exists():
        return None
    return json.loads(config_path.read_text())  # type: ignore[no-any-return]


def save_config(config_path: Path, config: dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")


def walk_dotpath(config: dict[str, Any], dotpath: str) -> Any:
    """Walk a dotpath like 'vars.slack.channel_id' and return the value, or None."""
    value: Any = config
    for part in dotpath.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
        if value is None:
            return None
    return value


def set_dotpath(config: dict[str, Any], dotpath: str, new_value: Any) -> bool:
    """Set a value at a dotpath. Returns True on success."""
    parts = dotpath.split(".")
    target: Any = config
    for part in parts[:-1]:
        if isinstance(target, dict):
            target = target.get(part)
        else:
            return False
        if target is None:
            return False
    if isinstance(target, dict):
        target[parts[-1]] = new_value
        return True
    return False


def cmd_resolve(skill_name: str) -> int:
    config_path = get_config_path()
    config = load_config(config_path)

    if config is None:
        print(f"error: config not found at {config_path}", file=sys.stderr)
        return 1

    skills = config.get("skills", {})

    if skill_name not in skills:
        print(f"warning: '{skill_name}' not in config (not yet migrated)", file=sys.stderr)
        return 2

    bindings = skills[skill_name]
    if not bindings:
        return 0

    for key, dotpath in bindings.items():
        value = walk_dotpath(config, dotpath)
        if value is None:
            print(f"warning: broken reference '{dotpath}' for key '{key}'", file=sys.stderr)
        else:
            print(f"{key}: {value}")

    return 0


def cmd_set(skill_name: str, key: str, value: str) -> int:
    config_path = get_config_path()
    config = load_config(config_path)

    if config is None:
        print(f"error: config not found at {config_path}", file=sys.stderr)
        return 1

    skills = config.get("skills", {})

    if skill_name not in skills:
        print(f"error: '{skill_name}' not in config", file=sys.stderr)
        return 2

    bindings = skills[skill_name]
    if key not in bindings:
        print(f"error: '{key}' is not a binding for '{skill_name}'", file=sys.stderr)
        return 3

    dotpath = bindings[key]

    # Try to parse value as JSON (for lists, numbers, booleans)
    try:
        parsed_value = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        parsed_value = value

    if not set_dotpath(config, dotpath, parsed_value):
        print(f"error: could not set '{dotpath}'", file=sys.stderr)
        return 4

    save_config(config_path, config)
    print(f"updated {key} ({dotpath}) = {parsed_value}")
    return 0


def _usage(msg: str | None = None) -> int:
    if msg:
        print(msg, file=sys.stderr)
    print("usage: skillctx-resolve.py <resolve|set> <skill-name> [key] [value]")
    return 1 if msg else 0


def main() -> int:
    if len(sys.argv) < 2:
        return _usage("error: no command provided")

    command = sys.argv[1]

    if command in ("-h", "--help"):
        return _usage()

    if command == "resolve":
        if len(sys.argv) != 3:
            return _usage()
        return cmd_resolve(sys.argv[2])

    elif command == "set":
        if len(sys.argv) != 5:
            return _usage()
        return cmd_set(sys.argv[2], sys.argv[3], sys.argv[4])

    else:
        return _usage(f"error: unknown command '{command}'")


if __name__ == "__main__":
    sys.exit(main())
