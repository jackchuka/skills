#!/usr/bin/env python3
"""Tests for render.py — feed sample JSON, assert HTML structure."""

import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
SCRIPTS = HERE.parent.parent / "gh-org-chart" / "scripts"
FIXTURE = HERE / "fixtures" / "sample-org.json"


def run_render(json_path: pathlib.Path) -> pathlib.Path:
    """Run render.py against json_path. Returns the produced HTML path."""
    subprocess.check_call([sys.executable, str(SCRIPTS / "render.py"), str(json_path)])
    return json_path.with_suffix(".html").parent / json_path.name.replace("-org.json", "-org.html")


def test_render() -> None:
    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        in_path = td_path / "acme-org.json"
        in_path.write_text(FIXTURE.read_text())

        out_path = run_render(in_path)
        assert out_path.exists(), f"missing output {out_path}"
        html = out_path.read_text()

        # Skeleton assertions
        assert html.startswith("<!DOCTYPE html>"), "missing doctype"
        assert "</html>" in html, "unclosed <html>"
        assert "prefers-color-scheme" in html, "missing dark-mode CSS"

        # JSON embedded
        assert '<script type="application/json" id="data">' in html, "missing data script tag"
        embedded = html.split('id="data">', 1)[1].split("</script>", 1)[0]
        data = json.loads(embedded)
        assert data["org"] == "acme"
        assert len(data["teams"]) == 3

        # Header shows org and timestamp
        assert "acme" in html
        assert "2026-05-15" in html

        # Size budget
        size = out_path.stat().st_size
        assert size < 1_000_000, f"output too big: {size} bytes"

        # Tree renders all team names and count pills
        for team in data["teams"]:
            assert team["name"] in html, f"missing team name {team['name']}"
            pill = f"{len(team['repos'])} &middot; {len(team['members'])}"
            assert pill in html, f"missing count pill for {team['name']}: {pill}"

        # Hierarchy: child team should be nested under parent in source order
        platform_idx = html.find(">Platform<")
        data_platform_idx = html.find(">Data Platform<")
        product_idx = html.find(">Product<")
        assert platform_idx < data_platform_idx < product_idx, (
            "expected order Platform → Data Platform → Product (depth-first)"
        )

        # Connector class is present
        assert "tree-connector" in html, "missing connector styling hook"

        # JS includes click-select wiring
        assert "addEventListener('click'" in html or 'addEventListener("click"' in html, (
            "missing click handler"
        )
        assert "renderDetail" in html, "missing renderDetail function"

        # All member logins appear somewhere (avatars or text)
        for team in data["teams"]:
            for login in team["members"]:
                assert login in html, f"missing member {login}"

        # All repo names appear
        for team in data["teams"]:
            for repo in team["repos"]:
                assert repo["name"] in html, f"missing repo {repo['name']}"

        # All CODEOWNERS paths appear
        for team in data["teams"]:
            for repo in team["repos"]:
                for path in repo.get("codeowner_paths", []):
                    assert path in html, f"missing codeowner path {path}"

        # Filter input present
        assert 'id="filter"' in html, "missing filter input"
        assert "applyFilter" in html, "missing applyFilter function"
