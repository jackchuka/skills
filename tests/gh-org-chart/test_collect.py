"""Tests for collect.sh — invoke with a fake `gh` shim on PATH, diff against golden JSON."""

import json
import os
import pathlib
import subprocess

import pytest

HERE = pathlib.Path(__file__).parent
SCRIPTS = HERE.parent.parent / "gh-org-chart" / "scripts"
SHIM = HERE / "fixtures" / "gh-shim"
GOLDEN = HERE / "golden"

CASES = [
    ("teams-only", ["--no-members", "--no-codeowners"]),
    ("with-members", ["--no-codeowners"]),
    ("with-repos", ["--no-codeowners"]),
    ("full", []),
]


@pytest.mark.parametrize("name,flags", CASES)
def test_collect(name: str, flags: list[str]) -> None:
    env = {**os.environ, "PATH": f"{SHIM}{os.pathsep}{os.environ['PATH']}"}
    out = subprocess.check_output(
        ["bash", str(SCRIPTS / "collect.sh"), "acme", *flags],
        env=env,
        text=True,
    )
    got = json.loads(out)
    got["collected_at"] = "NORMALIZED"
    expected = json.loads((GOLDEN / f"acme-{name}.json").read_text())
    assert got == expected
