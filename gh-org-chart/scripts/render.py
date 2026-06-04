#!/usr/bin/env python3
"""Render an HTML org explorer from a collect.sh JSON file.

Four views live in the same single-file HTML:
  - Overview: at-a-glance org dashboard (default landing).
  - Teams: hierarchical tree.
  - Users: flat list of every member across teams.
  - Repos: flat list of every repo seen across teams.
  - Chart: indented full-org tree (teams + members).
The detail pane cross-links between teams, users, and repos, every entity
deep-links via the URL hash, and every entity links out to GitHub.

Data model note: team `members` are objects: [{login, role}], role is
"maintainer" or "member".
"""

import json
import pathlib
import sys

CSS = """
:root {
  --bg: #fbfbfd; --bg-subtle: #f1f1f4; --panel: #ffffff; --panel-2: #f7f7f9;
  --border: #e4e4ea; --border-strong: #d4d4dc;
  --text: #1d1d1f; --muted: #6e6e76; --faint: #9a9aa2;
  --accent: #5e5ce6; --accent-soft: rgba(94,92,230,0.10); --accent-line: rgba(94,92,230,0.35);
  --selected-bg: rgba(94,92,230,0.09);
  --perm-admin: #cf222e; --perm-admin-bg: rgba(207,34,46,0.10);
  --perm-maintain: #9a6700; --perm-maintain-bg: rgba(154,103,0,0.12);
  --perm-push: #0969da; --perm-push-bg: rgba(9,105,218,0.10);
  --perm-muted: #6e7781; --perm-muted-bg: rgba(110,119,129,0.10);
  --shadow: 0 1px 2px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #161618; --bg-subtle: #1c1c1f; --panel: #202023; --panel-2: #26262a;
    --border: #303034; --border-strong: #3c3c42;
    --text: #f5f5f7; --muted: #9a9aa2; --faint: #6e6e76;
    --accent: #7d7bff; --accent-soft: rgba(125,123,255,0.14); --accent-line: rgba(125,123,255,0.45);
    --selected-bg: rgba(125,123,255,0.16);
    --perm-admin: #ff7b72; --perm-admin-bg: rgba(255,123,114,0.14);
    --perm-maintain: #e3b341; --perm-maintain-bg: rgba(227,179,65,0.14);
    --perm-push: #6cb6ff; --perm-push-bg: rgba(108,182,255,0.14);
    --perm-muted: #9aa0a8; --perm-muted-bg: rgba(154,160,168,0.13);
    --shadow: 0 1px 2px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.3);
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
  background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.5;
  -webkit-font-smoothing: antialiased; }
svg { display: inline-block; vertical-align: -0.13em; fill: currentColor; }

header { padding: 0 18px; height: 52px; border-bottom: 1px solid var(--border);
  background: var(--panel); display: flex; gap: 14px; align-items: center;
  position: sticky; top: 0; z-index: 10; }
header .brand { display: flex; align-items: baseline; gap: 10px; min-width: 0; }
header h1 { margin: 0; font-size: 15px; font-weight: 650; letter-spacing: -0.01em;
  cursor: pointer; white-space: nowrap; }
header h1:hover { color: var(--accent); }
header .ts { color: var(--faint); font-size: 11px; white-space: nowrap; }
header .org-ext { color: var(--faint); display: inline-flex; }
header .org-ext:hover { color: var(--accent); }

.view-switcher { display: flex; gap: 2px; margin-left: auto;
  background: var(--bg-subtle); border: 1px solid var(--border); border-radius: 9px; padding: 3px; }
.view-switcher button { padding: 5px 13px; font-size: 12px; font-weight: 600;
  background: transparent; color: var(--muted); border: none; border-radius: 6px;
  cursor: pointer; font-family: inherit; transition: color .12s, background .12s; }
.view-switcher button:hover { color: var(--text); }
.view-switcher button.active { background: var(--panel); color: var(--accent);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08); }

main { display: grid; grid-template-columns: minmax(280px, 32%) 1fr;
  grid-template-rows: minmax(0, 1fr); height: calc(100vh - 52px); }
@media (max-width: 860px) { main { grid-template-columns: 1fr; grid-template-rows: none; height: auto; } }
body.chart-mode main { grid-template-columns: 1fr; }
body.chart-mode #tree { display: none; }
#tree, #detail { overflow: auto; min-height: 0; }
#tree { border-right: 1px solid var(--border); background: var(--panel); padding: 0 10px 32px;
  overflow-x: hidden; }
#detail { padding: 22px 26px 40px; }
#detail .empty { color: var(--muted); }
.kbd { font-family: ui-monospace, monospace; font-size: 11px; padding: 1px 5px;
  border: 1px solid var(--border-strong); border-bottom-width: 2px; border-radius: 5px;
  background: var(--panel-2); color: var(--muted); }
"""

# Left tree (teams/users/repos lists) + filter bar.
CSS += """
.filter-bar { position: sticky; top: 0; background: var(--panel); z-index: 2;
  padding: 12px 2px 10px; margin-bottom: 4px;
  display: flex; align-items: center; gap: 8px; }
.filter-bar .ic { color: var(--faint); display: inline-flex; }
.filter-bar input { flex: 1; padding: 7px 10px; border: 1px solid var(--border); min-width: 0;
  border-radius: 8px; background: var(--bg-subtle); color: var(--text); font-size: 13px;
  font-family: inherit; }
.filter-bar input:focus { outline: none; border-color: var(--accent); background: var(--panel);
  box-shadow: 0 0 0 3px var(--accent-soft); }
.view-pane[hidden] { display: none; }

.tree-row { display: flex; align-items: center; gap: 8px; padding: 7px 8px;
  border-radius: 8px; cursor: pointer; position: relative; }
.tree-row:hover { background: var(--selected-bg); }
.tree-row.selected { background: var(--selected-bg);
  box-shadow: inset 0 0 0 1px var(--accent-line); }
.tree-row .chev { width: 12px; color: var(--faint); font-size: 9px; text-align: center; flex-shrink: 0; }
.tree-row .ic { color: var(--muted); display: inline-flex; flex-shrink: 0; }
.tree-row .avatar { width: 22px; height: 22px; border-radius: 50%; background: var(--border);
  flex-shrink: 0; object-fit: cover; }
.tree-row .name { font-weight: 600; white-space: nowrap; min-width: 0;
  overflow: hidden; text-overflow: ellipsis; }
.tree-row .desc { color: var(--muted); font-size: 11.5px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0; }
.tree-row .spacer { flex: 1; min-width: 8px; }
.tree-row .perm-cell { display: inline-flex; align-items: center; flex-shrink: 0; }
.tree-row .ext { opacity: 0; color: var(--faint); display: inline-flex; padding: 2px;
  border-radius: 5px; flex-shrink: 0; transition: opacity .1s; }
.tree-row:hover .ext { opacity: 1; }
.tree-row .ext:hover { color: var(--accent); background: var(--bg-subtle); }

.counts { display: inline-flex; gap: 7px; flex-shrink: 0; }
.metric { display: inline-flex; align-items: center; gap: 3px; color: var(--muted);
  font-size: 11px; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.metric .ic { color: var(--faint); }
.metric.zero { opacity: 0.4; }

.tree-children { position: relative; padding-left: 18px; margin-top: 1px; }
.tree-connector { position: absolute; left: 13px; top: 2px; bottom: 6px;
  width: 1px; background: var(--border); }
.tree-children.collapsed { display: none; }
.tree-row.dim { opacity: 0.35; }
.tree-row.hide { display: none; }
.archive-toggle { display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px;
  color: var(--muted); white-space: nowrap; cursor: pointer; user-select: none; flex-shrink: 0; }
.archive-toggle[hidden] { display: none; }
.archive-toggle input { accent-color: var(--accent); cursor: pointer; margin: 0; }
"""

# Detail pane.
CSS += """
.detail .crumb { margin-bottom: 14px; }
.detail .crumb a { color: var(--muted); text-decoration: none; font-size: 12.5px;
  display: inline-flex; align-items: center; gap: 5px; }
.detail .crumb a:hover { color: var(--accent); }
.detail-head { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 8px; }
.detail-head .ava { width: 52px; height: 52px; border-radius: 14px; background: var(--border);
  flex-shrink: 0; object-fit: cover; }
.detail-head .ava.round { border-radius: 50%; }
.detail-head .glyph { width: 52px; height: 52px; border-radius: 14px; flex-shrink: 0;
  display: grid; place-items: center; background: var(--accent-soft); color: var(--accent); }
.detail-head .glyph svg { width: 26px; height: 26px; }
.detail h2 { margin: 0; font-size: 22px; letter-spacing: -0.02em; font-weight: 680; line-height: 1.15; }
.detail h2 a { color: inherit; text-decoration: none; }
.detail h2 a:hover { color: var(--accent); }
.detail .sub { color: var(--muted); font-size: 13px; margin-top: 3px; }
.detail .gh-link { display: inline-flex; align-items: center; gap: 5px; margin-top: 8px;
  font-size: 12.5px; color: var(--accent); text-decoration: none; font-weight: 550;
  padding: 4px 10px; border: 1px solid var(--border); border-radius: 8px; }
.detail .gh-link:hover { border-color: var(--accent); background: var(--accent-soft); }

.detail .section { margin-top: 26px; }
.detail .label { text-transform: uppercase; font-size: 11px; color: var(--muted);
  letter-spacing: 0.06em; font-weight: 650; margin-bottom: 11px;
  display: flex; align-items: center; gap: 8px; }
.detail .label .n { color: var(--faint); font-weight: 600; }

.members { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 4px; }
.member { display: flex; align-items: center; gap: 8px; padding: 5px 7px;
  border-radius: 8px; cursor: pointer; min-width: 0; }
.member:hover { background: var(--selected-bg); }
.member img { width: 28px; height: 28px; border-radius: 50%; background: var(--border);
  flex-shrink: 0; object-fit: cover; }
.member .m-name { font-size: 13px; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; min-width: 0; }
.member .role { color: var(--perm-maintain); display: inline-flex; flex-shrink: 0; }

.repo-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.repo-table th, .repo-table td { text-align: left; padding: 8px 10px;
  border-bottom: 1px solid var(--border); vertical-align: middle; }
.repo-table tr:last-child td { border-bottom: none; }
.repo-table tbody tr { cursor: pointer; }
.repo-table tbody tr:hover { background: var(--selected-bg); }
.repo-table th { color: var(--muted); font-weight: 600; font-size: 10.5px;
  text-transform: uppercase; letter-spacing: 0.05em; }
.repo-table a { color: var(--text); text-decoration: none; font-weight: 550; }
.repo-table tbody tr:hover a.r-name { color: var(--accent); }
.repo-table .ext { color: var(--faint); display: inline-flex; margin-left: 6px; opacity: 0; }
.repo-table tbody tr:hover .ext { opacity: 1; }
.repo-table .ext:hover { color: var(--accent); }

.perm { font-family: ui-monospace, monospace; font-size: 11px; font-weight: 600;
  padding: 2px 8px; border-radius: 20px; text-transform: lowercase; white-space: nowrap;
  border: 1px solid transparent; }
.perm-admin    { color: var(--perm-admin);    background: var(--perm-admin-bg);    border-color: var(--perm-admin); }
.perm-maintain { color: var(--perm-maintain); background: var(--perm-maintain-bg); border-color: var(--perm-maintain); }
.perm-push     { color: var(--perm-push);     background: var(--perm-push-bg); }
.perm-muted    { color: var(--perm-muted);    background: var(--perm-muted-bg); }
.perm-legend { display: flex; flex-wrap: wrap; gap: 6px; }

.arch { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 600;
  color: var(--muted); background: var(--bg-subtle); border: 1px solid var(--border);
  border-radius: 20px; padding: 2px 8px; white-space: nowrap; }
.arch svg { opacity: 0.85; }
.r-name.archived { color: var(--muted); }
.r-name.archived svg { margin-right: 4px; opacity: 0.7; vertical-align: -0.1em; }
.repo-table tbody tr:hover a.r-name.archived { color: var(--accent); }
.tree-row.archived .name { color: var(--muted); }
.tree-row .arch-ic { color: var(--faint); display: inline-flex; flex-shrink: 0; }

.paths { display: flex; flex-wrap: wrap; gap: 4px; }
.path { font-family: ui-monospace, monospace; font-size: 11px;
  padding: 2px 7px; background: var(--bg-subtle); border: 1px solid var(--border);
  border-radius: 5px; color: var(--muted); }
.chips { display: flex; flex-wrap: wrap; gap: 7px; }
.chip { padding: 5px 11px; background: var(--panel-2); border: 1px solid var(--border);
  border-radius: 20px; font-size: 12.5px; cursor: pointer; color: var(--text);
  text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }
.chip:hover { border-color: var(--accent); color: var(--accent); }
.chip .role { color: var(--perm-maintain); display: inline-flex; }
"""

# Overview dashboard.
CSS += """
.ov-hero h2 { font-size: 26px; letter-spacing: -0.025em; margin: 0; font-weight: 700; }
.ov-hero .sub { color: var(--muted); margin-top: 4px; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px; margin: 22px 0 4px; }
.stat-card { background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
  padding: 16px 18px; box-shadow: var(--shadow); }
.stat-card .v { font-size: 30px; font-weight: 720; letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums; line-height: 1; }
.stat-card .k { color: var(--muted); font-size: 12.5px; margin-top: 7px;
  display: flex; align-items: center; gap: 6px; }
.stat-card .k .ic { color: var(--faint); }

.ov-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; margin-top: 26px; }
@media (max-width: 1080px) { .ov-cols { grid-template-columns: 1fr; } }
.bar-list { display: flex; flex-direction: column; gap: 3px; }
.bar-row { display: flex; align-items: center; gap: 10px; padding: 6px 8px;
  border-radius: 8px; cursor: pointer; }
.bar-row:hover { background: var(--selected-bg); }
.bar-row .bl { font-weight: 600; white-space: nowrap; min-width: 0; overflow: hidden;
  text-overflow: ellipsis; flex-shrink: 0; max-width: 42%; }
.bar-row .track { flex: 1; height: 7px; background: var(--bg-subtle); border-radius: 4px;
  overflow: hidden; }
.bar-row .fill { height: 100%; background: var(--accent); border-radius: 4px; }
.bar-row.admin .fill { background: var(--perm-admin); }
.bar-row .bv { color: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums;
  width: 2.5em; text-align: right; flex-shrink: 0; }
"""

# Chart view.
CSS += """
.org-chart { padding: 4px 2px 24px; font-size: 13px; }
.org-chart .legend { color: var(--muted); font-size: 12px; margin: 4px 0 14px; }
.chart-toolbar { display: flex; gap: 8px; margin-bottom: 14px; align-items: center;
  position: sticky; top: 0; background: var(--bg); padding: 8px 0; z-index: 1; }
.chart-toolbar input { flex: 1; max-width: 380px; padding: 7px 10px;
  border: 1px solid var(--border); border-radius: 8px; background: var(--panel);
  color: var(--text); font-size: 13px; font-family: inherit; }
.chart-toolbar input:focus { outline: none; border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft); }
.chart-toolbar button { padding: 6px 13px; font-size: 12px; font-weight: 600;
  background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
  cursor: pointer; color: var(--text); font-family: inherit; }
.chart-toolbar button:hover { border-color: var(--accent); color: var(--accent); }
.chart-toolbar .stat { color: var(--muted); font-size: 12px; }
.h-tree, .h-tree ul { list-style: none; margin: 0; padding: 0; position: relative; }
.h-tree ul { padding-left: 28px; }
.h-tree li { position: relative; padding: 3px 0 3px 22px; line-height: 1.6; }
.h-tree > li { padding-left: 0; }
.h-tree ul > li::before {
  content: ""; position: absolute; left: 0; top: 0; height: 1.02em;
  width: 18px; border-left: 1px solid var(--border); border-bottom: 1px solid var(--border);
  border-bottom-left-radius: 7px;
}
.h-tree ul > li::after {
  content: ""; position: absolute; left: 0; top: 1.02em; bottom: 0;
  border-left: 1px solid var(--border);
}
.h-tree ul > li:last-child::after { display: none; }
.h-node { display: inline-flex; align-items: center; gap: 6px; padding: 3px 9px;
  border-radius: 8px; cursor: pointer; border: 1px solid transparent; }
.h-node:hover { background: var(--selected-bg); border-color: var(--accent-line); }
.h-node.team { font-weight: 650; }
.h-node.team .ic { color: var(--muted); }
.h-node.user img { width: 19px; height: 19px; border-radius: 50%; object-fit: cover; }
.h-node .role { color: var(--perm-maintain); display: inline-flex; }
.h-node .count { color: var(--faint); font-size: 11px; font-weight: 500; margin-left: 3px;
  font-variant-numeric: tabular-nums; }
.h-node.org { background: var(--panel); border: 1px solid var(--border); font-weight: 700; }
.h-node .chev { color: var(--faint); font-size: 9px; width: 12px; text-align: center;
  display: inline-block; transition: transform 0.12s; cursor: pointer;
  padding: 2px; margin: -2px 0 -2px -3px; border-radius: 4px; }
.h-node .chev:hover { background: var(--bg-subtle); color: var(--text); }
.h-tree li[data-collapsed="true"] > ul { display: none; }
.h-tree li[data-collapsed="true"] > .h-node .chev { transform: rotate(-90deg); }
.h-tree li.hide { display: none; }
.h-node.highlight { background: var(--accent-soft); border-color: var(--accent); }
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__ORG__ — org chart</title>
  <style>__CSS__</style>
</head>
<body>
<header>
  <div class="brand">
    <h1 id="home" title="Overview">__ORG__</h1>
    <a class="org-ext" id="org-ext" target="_blank" rel="noopener" title="Open org on GitHub"></a>
    <span class="ts">collected __TS__</span>
  </div>
  <div class="view-switcher" role="tablist">
    <button data-view="teams" class="active" role="tab">Teams</button>
    <button data-view="users" role="tab">Users</button>
    <button data-view="repos" role="tab">Repos</button>
    <button data-view="chart" role="tab">Chart</button>
  </div>
</header>
<main>
  <aside id="tree">
    <div class="filter-bar">
      <span class="ic" id="filter-ic" aria-hidden="true"></span>
      <input id="filter" type="search" placeholder="Filter…  ( / )">
      <label class="archive-toggle" id="archive-toggle" hidden title="Hide archived repositories">
        <input type="checkbox" id="hide-archived" checked>hide archived</label>
    </div>
    <div id="view-teams" class="view-pane">__TREE__</div>
    <div id="view-users" class="view-pane" hidden></div>
    <div id="view-repos" class="view-pane" hidden></div>
  </aside>
  <section id="detail"></section>
</main>
<script type="application/json" id="data">__DATA__</script>
<script>
(function() {
  const data = JSON.parse(document.getElementById('data').textContent);
  const ORG = data.org;
  const teamBySlug = Object.fromEntries(data.teams.map(t => [t.slug, t]));
  const teamChildren = {};
  for (const t of data.teams) {
    if (t.parent) (teamChildren[t.parent] = teamChildren[t.parent] || []).push(t);
  }

  // ---------- Icons (Octicons, 16px) ----------
  const I = {
    people: '<svg width="14" height="14" viewBox="0 0 16 16"><path d="M2 5.5a3.5 3.5 0 1 1 5.898 2.549 5.508 5.508 0 0 1 3.034 4.084.75.75 0 1 1-1.482.235 4 4 0 0 0-7.9 0 .75.75 0 0 1-1.482-.236A5.507 5.507 0 0 1 3.102 8.05 3.493 3.493 0 0 1 2 5.5ZM11 4a3.001 3.001 0 0 1 2.22 5.018 5.01 5.01 0 0 1 2.56 3.012.749.749 0 0 1-.885.954.752.752 0 0 1-.549-.514 3.507 3.507 0 0 0-2.522-2.372.75.75 0 0 1-.574-.73v-.352a.75.75 0 0 1 .416-.672A1.5 1.5 0 0 0 11 5.5.75.75 0 0 1 11 4Zm-5.5-.5a2 2 0 1 0-.001 3.999A2 2 0 0 0 5.5 3.5Z"/></svg>',
    repo: '<svg width="13" height="13" viewBox="0 0 16 16"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"/></svg>',
    ext: '<svg width="12" height="12" viewBox="0 0 16 16"><path d="M3.75 2h3.5a.75.75 0 0 1 0 1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 2Zm6.854-1h4.146a.25.25 0 0 1 .25.25v4.146a.25.25 0 0 1-.427.177L13.03 4.03 9.28 7.78a.751.751 0 0 1-1.06-1.06l3.75-3.75-1.543-1.543A.25.25 0 0 1 10.604 1Z"/></svg>',
    shield: '<svg width="12" height="12" viewBox="0 0 16 16"><path d="M7.467.133a1.748 1.748 0 0 1 1.066 0l5.25 1.68A1.75 1.75 0 0 1 15 3.48V7c0 1.566-.32 3.182-1.303 4.682-.983 1.498-2.585 2.813-5.032 3.855a1.697 1.697 0 0 1-1.33 0c-2.447-1.042-4.049-2.357-5.032-3.855C1.32 10.182 1 8.566 1 7V3.48a1.75 1.75 0 0 1 1.217-1.667Z"/></svg>',
    search: '<svg width="14" height="14" viewBox="0 0 16 16"><path d="M10.68 11.74a6 6 0 0 1-7.922-8.982 6 6 0 0 1 8.982 7.922l3.04 3.04a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215ZM11.5 7a4.499 4.499 0 1 0-8.997 0A4.499 4.499 0 0 0 11.5 7Z"/></svg>',
    back: '<svg width="12" height="12" viewBox="0 0 16 16"><path d="M7.78 12.53a.75.75 0 0 1-1.06 0L2.47 8.28a.75.75 0 0 1 0-1.06l4.25-4.25a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L4.81 7.25h7.44a.75.75 0 0 1 0 1.5H4.81l2.97 2.97a.75.75 0 0 1 0 1.06Z"/></svg>',
    archive: '<svg width="12" height="12" viewBox="0 0 16 16"><path d="M1.75 2.5a.25.25 0 0 0-.25.25v1.5c0 .138.112.25.25.25h12.5a.25.25 0 0 0 .25-.25v-1.5a.25.25 0 0 0-.25-.25Zm-.25 4.516A1.75 1.75 0 0 1 0 4.25v-1.5C0 1.784.784 1 1.75 1h12.5c.966 0 1.75.784 1.75 1.75v1.5a1.75 1.75 0 0 1-1.5 1.732V13.25A1.75 1.75 0 0 1 12.75 15h-9.5A1.75 1.75 0 0 1 1.5 13.25Zm1.5.234v6.5c0 .138.112.25.25.25h9.5a.25.25 0 0 0 .25-.25v-6.5Zm3.75 1.5a.75.75 0 0 0 0 1.5h2.5a.75.75 0 0 0 0-1.5Z"/></svg>',
  };
  document.getElementById('filter-ic').innerHTML = I.search;
  const orgExt = document.getElementById('org-ext');
  orgExt.innerHTML = I.ext;
  orgExt.href = 'https://github.com/orgs/' + encodeURIComponent(ORG) + '/teams';

  const PERM_ORDER = { pull: 0, triage: 1, push: 2, maintain: 3, admin: 4 };
  function permRank(p) { return PERM_ORDER[p] == null ? -1 : PERM_ORDER[p]; }
  function permClass(p) {
    if (p === 'admin') return 'perm-admin';
    if (p === 'maintain') return 'perm-maintain';
    if (p === 'push') return 'perm-push';
    return 'perm-muted';
  }
  function permPill(p) { return `<span class="perm ${permClass(p)}">${esc(p)}</span>`; }
  function memberList(t) { return (t.members || []); }            // [{login, role}]
  function memberLogins(t) { return memberList(t).map(m => m.login); }

  // ---------- Indexes ----------
  // login -> { login, teams: [{slug, role}], repos: { name: bestPerm } }
  const userIndex = {};
  for (const t of data.teams) {
    for (const m of memberList(t)) {
      const u = userIndex[m.login] || (userIndex[m.login] = { login: m.login, teams: [], repos: {} });
      if (!u.teams.some(x => x.slug === t.slug)) u.teams.push({ slug: t.slug, role: m.role });
      for (const r of (t.repos || [])) {
        const cur = u.repos[r.name];
        if (cur == null || permRank(r.permission) > permRank(cur)) u.repos[r.name] = r.permission;
      }
    }
  }
  const users = Object.values(userIndex).sort((a, b) =>
    a.login.toLowerCase().localeCompare(b.login.toLowerCase()));

  // name -> { name, teams: [{slug, permission, paths}], bestPerm }
  const repoIndex = {};
  for (const t of data.teams) {
    for (const r of (t.repos || [])) {
      const ri = repoIndex[r.name] || (repoIndex[r.name] = { name: r.name, teams: [], bestPerm: null, archived: false });
      ri.teams.push({ slug: t.slug, permission: r.permission, paths: r.codeowner_paths || [] });
      if (r.archived) ri.archived = true;
      if (ri.bestPerm == null || permRank(r.permission) > permRank(ri.bestPerm)) ri.bestPerm = r.permission;
    }
  }
  const repos = Object.values(repoIndex).sort((a, b) =>
    a.name.toLowerCase().localeCompare(b.name.toLowerCase()));

  const teamRoots = data.teams.filter(t => !t.parent || !teamBySlug[t.parent])
    .sort((a, b) => a.name.localeCompare(b.name));

  const detail = document.getElementById('detail');
  const filterEl = document.getElementById('filter');
  const hideArchivedEl = document.getElementById('hide-archived');
  const archiveToggle = document.getElementById('archive-toggle');
  const panes = {
    teams: document.getElementById('view-teams'),
    users: document.getElementById('view-users'),
    repos: document.getElementById('view-repos'),
  };
  let listView = 'teams';   // which left list is shown
  let mode = 'overview';    // overview | entity | chart

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function avatarUrl(login, size) {
    return `https://github.com/${encodeURIComponent(login)}.png?size=${size || 40}`;
  }
  function shortRepo(name) { return name.includes('/') ? name.split('/').slice(1).join('/') : name; }
  function ghUrl(kind, id) {
    if (kind === 'team') return `https://github.com/orgs/${encodeURIComponent(ORG)}/teams/${encodeURIComponent(id)}`;
    if (kind === 'user') return `https://github.com/${encodeURIComponent(id)}`;
    if (kind === 'repo') return `https://github.com/${id.split('/').map(encodeURIComponent).join('/')}`;
    return '#';
  }
  function extLink(kind, id) {
    return `<a class="ext" href="${esc(ghUrl(kind, id))}" target="_blank" rel="noopener"
      title="Open on GitHub" data-ext>${I.ext}</a>`;
  }
  function countsHtml(memberCount, repoCount) {
    return `<span class="counts">
      <span class="metric ${memberCount ? '' : 'zero'}" title="${memberCount} member(s)">${I.people}${memberCount}</span>
      <span class="metric ${repoCount ? '' : 'zero'}" title="${repoCount} repo(s)">${I.repo}${repoCount}</span>
    </span>`;
  }
  const roleBadge = r => r === 'maintainer' ? `<span class="role" title="maintainer">${I.shield}</span>` : '';
  const isArchived = name => !!(repoIndex[name] && repoIndex[name].archived);
  const archiveTag = `<span class="arch" title="Archived — read-only">${I.archive}archived</span>`;
  // Repo name link for tables: muted + archive glyph when archived, with an ext link.
  function repoNameCell(name) {
    const arch = isArchived(name);
    return `<a class="r-name${arch ? ' archived' : ''}" data-go-kind="repo" data-go-id="${esc(name)}"
      ${arch ? 'title="Archived — read-only"' : ''}>${arch ? I.archive : ''}${esc(shortRepo(name))}</a>${extLink('repo', name)}`;
  }

  // ---------- Left lists (users & repos rendered client-side) ----------
  function renderUsersTree() {
    panes.users.innerHTML = users.map(u =>
      `<div class="tree-row" data-kind="user" data-id="${esc(u.login)}">
        <img class="avatar" loading="lazy" src="${esc(avatarUrl(u.login, 28))}" alt="">
        <span class="name">${esc(u.login)}</span>
        <span class="spacer"></span>
        ${extLink('user', u.login)}
        ${countsHtml(u.teams.length, Object.keys(u.repos).length)}
      </div>`).join('');
  }
  function renderReposTree() {
    panes.repos.innerHTML = repos.map(r =>
      `<div class="tree-row${r.archived ? ' archived' : ''}" data-kind="repo" data-id="${esc(r.name)}" title="${esc(r.name)}${r.archived ? ' (archived)' : ''}">
        <span class="ic" title="${r.archived ? 'Archived — read-only' : ''}">${r.archived ? I.archive : I.repo}</span>
        <span class="name">${esc(shortRepo(r.name))}</span>
        <span class="perm-cell">${permPill(r.bestPerm || 'pull')}</span>
        <span class="spacer"></span>
        ${extLink('repo', r.name)}
        <span class="metric" title="${r.teams.length} team grant(s)">${I.people}${r.teams.length}</span>
      </div>`).join('');
  }
  renderUsersTree();
  renderReposTree();

  // ---------- Overview ----------
  function renderOverview() {
    const maintainerLogins = new Set();
    for (const u of users) if (u.teams.some(x => x.role === 'maintainer')) maintainerLogins.add(u.login);
    const adminRepos = repos.filter(r => r.bestPerm === 'admin');
    const archivedRepos = repos.filter(r => r.archived);

    const topTeams = data.teams.slice()
      .sort((a, b) => (b.members || []).length - (a.members || []).length).slice(0, 8);
    const maxTeam = Math.max(1, ...topTeams.map(t => (t.members || []).length));
    const teamBars = topTeams.map(t => {
      const n = (t.members || []).length;
      return `<div class="bar-row" data-go-kind="team" data-go-id="${esc(t.slug)}">
        <span class="bl">${esc(t.name)}</span>
        <span class="track"><span class="fill" style="width:${(n / maxTeam * 100).toFixed(1)}%"></span></span>
        <span class="bv">${n}</span></div>`;
    }).join('');

    const topAdmin = adminRepos.slice()
      .sort((a, b) => b.teams.length - a.teams.length).slice(0, 8);
    const maxAdmin = Math.max(1, ...topAdmin.map(r => r.teams.length));
    const adminBars = topAdmin.length ? topAdmin.map(r =>
      `<div class="bar-row admin" data-go-kind="repo" data-go-id="${esc(r.name)}">
        <span class="bl">${esc(shortRepo(r.name))}</span>
        <span class="track"><span class="fill" style="width:${(r.teams.length / maxAdmin * 100).toFixed(1)}%"></span></span>
        <span class="bv">${r.teams.length}</span></div>`).join('')
      : '<p class="empty">No repos with admin-level team grants.</p>';

    const card = (v, k, icon) => `<div class="stat-card"><div class="v">${v}</div>
      <div class="k">${icon}${k}</div></div>`;

    detail.innerHTML = `
      <div class="detail ov-hero">
        <h2>${esc(ORG)}</h2>
        <div class="sub">GitHub organization overview</div>
        <div class="stat-grid">
          ${card(data.teams.length, 'teams', I.people)}
          ${card(users.length, 'distinct members', I.people)}
          ${card(maintainerLogins.size, 'maintainers', I.shield)}
          ${card(repos.length, 'repos', I.repo)}
          ${card(adminRepos.length, 'repos w/ admin grant', I.repo)}
          ${card(archivedRepos.length, 'archived repos', I.archive)}
        </div>
        <div class="ov-cols">
          <div class="section" style="margin-top:0">
            <div class="label">${I.people}<span>Largest teams</span></div>
            <div class="bar-list">${teamBars}</div>
          </div>
          <div class="section" style="margin-top:0">
            <div class="label">${I.repo}<span>Most-shared admin repos</span></div>
            <div class="bar-list">${adminBars}</div>
          </div>
        </div>
        <div class="section">
          <div class="label"><span>Permission legend</span></div>
          <div class="perm-legend">${['admin','maintain','push','pull'].map(permPill).join('')}</div>
        </div>
      </div>`;
  }

  // ---------- Chart ----------
  let chartCollapsed = false;
  function descendantMembers(slug) {
    const set = new Set();
    const stack = [...(teamChildren[slug] || [])];
    while (stack.length) {
      const c = stack.pop();
      for (const m of memberList(c)) set.add(m.login);
      for (const cc of (teamChildren[c.slug] || [])) stack.push(cc);
    }
    return set;
  }
  function renderChartTeam(t) {
    const inherited = descendantMembers(t.slug);
    const direct = memberList(t).filter(m => !inherited.has(m.login));
    const members = direct.slice()
      .sort((a, b) => (b.role === 'maintainer') - (a.role === 'maintainer') ||
        a.login.toLowerCase().localeCompare(b.login.toLowerCase()))
      .map(m => `<li><span class="h-node user" data-go-kind="user" data-go-id="${esc(m.login)}">
        <img loading="lazy" src="${esc(avatarUrl(m.login, 24))}" alt="">${esc(m.login)}${roleBadge(m.role)}
      </span></li>`).join('');
    const subs = (teamChildren[t.slug] || []).slice()
      .sort((a, b) => a.name.localeCompare(b.name))
      .map(c => `<li>${renderChartTeam(c)}</li>`).join('');
    const hasChildren = !!(members || subs);
    const inner = hasChildren ? `<ul>${members}${subs}</ul>` : '';
    const chev = hasChildren ? `<span class="chev" data-toggle="collapse">&#9662;</span>` : '';
    const total = memberList(t).length;
    const countLabel = direct.length === total ? `${total}` : `${direct.length}/${total}`;
    return `<span class="h-node team" data-go-kind="team" data-go-id="${esc(t.slug)}">
      ${chev}<span class="ic">${I.people}</span>${esc(t.name)}<span class="count" title="direct/total members · repos">${countLabel} &middot; ${(t.repos || []).length}</span>
    </span>${inner}`;
  }
  function renderChart() {
    const roots = teamRoots.map(t => `<li>${renderChartTeam(t)}</li>`).join('');
    detail.innerHTML = `<div class="org-chart">
      <div class="chart-toolbar">
        <input id="chart-filter" type="search" placeholder="Filter teams, members…">
        <button data-chart-action="toggle-all">${chartCollapsed ? 'Expand all' : 'Collapse all'}</button>
        <span class="stat" id="chart-stat"></span>
      </div>
      <div class="legend">${data.teams.length} teams &middot; members shown under their direct team (subteam members not duplicated upward)</div>
      <ul class="h-tree">
        <li><span class="h-node org"><span class="chev" data-toggle="collapse">&#9662;</span>${esc(ORG)}</span>
          <ul>${roots}</ul>
        </li>
      </ul>
    </div>`;
    const f = document.getElementById('chart-filter');
    if (f) f.addEventListener('input', () => applyChartFilter(f.value));
    if (chartCollapsed) setAllCollapsed(true);
  }
  function setAllCollapsed(collapsed) {
    const chart = detail.querySelector('.org-chart');
    if (!chart) return;
    chart.querySelectorAll('li').forEach(li => {
      if (li.querySelector(':scope > ul')) li.dataset.collapsed = collapsed ? 'true' : 'false';
    });
    chartCollapsed = collapsed;
    const btn = chart.querySelector('[data-chart-action="toggle-all"]');
    if (btn) btn.textContent = collapsed ? 'Expand all' : 'Collapse all';
  }
  function applyChartFilter(raw) {
    const chart = detail.querySelector('.org-chart');
    if (!chart) return;
    const q = (raw || '').trim().toLowerCase();
    const lis = chart.querySelectorAll('.h-tree li');
    lis.forEach(li => li.classList.remove('hide'));
    chart.querySelectorAll('.h-node.highlight').forEach(n => n.classList.remove('highlight'));
    const stat = document.getElementById('chart-stat');
    if (!q) { if (stat) stat.textContent = ''; return; }
    chart.querySelectorAll('li[data-collapsed="true"]').forEach(li => li.dataset.collapsed = 'false');
    const matched = new Set();
    lis.forEach(li => {
      const node = li.querySelector(':scope > .h-node');
      if (node && node.textContent.toLowerCase().includes(q)) { matched.add(li); node.classList.add('highlight'); }
    });
    const visible = new Set();
    matched.forEach(li => {
      visible.add(li);
      li.querySelectorAll('li').forEach(d => visible.add(d));
      let p = li.parentElement;
      while (p && p !== chart) { if (p.tagName === 'LI') visible.add(p); p = p.parentElement; }
    });
    lis.forEach(li => { if (!visible.has(li)) li.classList.add('hide'); });
    if (stat) stat.textContent = `${matched.size} match${matched.size === 1 ? '' : 'es'}`;
  }

  // ---------- Detail renderers ----------
  function detailHead(opts) {
    const glyph = opts.avatar
      ? `<img class="ava ${opts.round ? 'round' : ''}" loading="lazy" src="${esc(opts.avatar)}" alt="">`
      : `<div class="glyph">${opts.icon || I.people}</div>`;
    return `<div class="detail-head">
      ${glyph}
      <div style="min-width:0">
        <h2><a href="${esc(opts.gh)}" target="_blank" rel="noopener">${esc(opts.title)}</a></h2>
        <div class="sub">${opts.sub}</div>
        <a class="gh-link" href="${esc(opts.gh)}" target="_blank" rel="noopener">${I.ext} Open on GitHub</a>
      </div>
    </div>`;
  }

  function renderTeamDetail(slug) {
    const t = teamBySlug[slug];
    if (!t) return renderOverview();
    const crumb = t.parent && teamBySlug[t.parent]
      ? `<div class="crumb"><a data-go-kind="team" data-go-id="${esc(t.parent)}">${I.back} ${esc(teamBySlug[t.parent].name)}</a></div>` : '';
    const ms = memberList(t).slice().sort((a, b) =>
      (b.role === 'maintainer') - (a.role === 'maintainer') ||
      a.login.toLowerCase().localeCompare(b.login.toLowerCase()));
    const members = ms.map(m =>
      `<div class="member" data-go-kind="user" data-go-id="${esc(m.login)}">
        <img loading="lazy" src="${esc(avatarUrl(m.login, 36))}" alt="">
        <span class="m-name">${esc(m.login)}</span>${roleBadge(m.role)}
      </div>`).join('');
    const reposSorted = (t.repos || []).slice()
      .sort((a, b) => permRank(b.permission) - permRank(a.permission) || a.name.localeCompare(b.name));
    const rows = reposSorted.map(r => {
      const paths = (r.codeowner_paths || []).map(p => `<span class="path">${esc(p)}</span>`).join('');
      return `<tr data-go-kind="repo" data-go-id="${esc(r.name)}">
        <td>${repoNameCell(r.name)}</td>
        <td>${permPill(r.permission)}</td>
        <td><div class="paths">${paths}</div></td>
      </tr>`;
    }).join('');
    const subteams = (teamChildren[t.slug] || []).map(c =>
      `<a class="chip" data-go-kind="team" data-go-id="${esc(c.slug)}">${I.people}${esc(c.name)}</a>`).join('');
    const maint = ms.filter(m => m.role === 'maintainer').length;

    detail.innerHTML = `<div class="detail">${crumb}
      ${detailHead({ title: t.name, gh: ghUrl('team', t.slug), icon: I.people,
        sub: `${esc(t.description || 'No description')} &middot; ${ms.length} member${ms.length===1?'':'s'}${maint?` (${maint} maintainer${maint===1?'':'s'})`:''} &middot; ${(t.repos||[]).length} repo${(t.repos||[]).length===1?'':'s'}` })}
      <div class="section">
        <div class="label">${I.people}<span>Members</span> <span class="n">${ms.length}</span></div>
        <div class="members">${members || '<span class="empty">none</span>'}</div>
      </div>
      <div class="section">
        <div class="label">${I.repo}<span>Repositories</span> <span class="n">${(t.repos||[]).length}</span></div>
        <table class="repo-table">
          <thead><tr><th>Repo</th><th>Permission</th><th>CODEOWNERS paths</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="3" class="empty">none</td></tr>'}</tbody>
        </table>
      </div>
      ${subteams ? `<div class="section"><div class="label"><span>Subteams</span></div><div class="chips">${subteams}</div></div>` : ''}
    </div>`;
  }

  function renderUserDetail(login) {
    const u = userIndex[login];
    if (!u) return renderOverview();
    const teamChips = u.teams.slice()
      .sort((a, b) => (b.role === 'maintainer') - (a.role === 'maintainer'))
      .map(x => {
        const t = teamBySlug[x.slug];
        return `<a class="chip" data-go-kind="team" data-go-id="${esc(x.slug)}">${I.people}${esc(t ? t.name : x.slug)}${roleBadge(x.role)}</a>`;
      }).join('');
    const userRepos = Object.entries(u.repos)
      .sort((a, b) => permRank(b[1]) - permRank(a[1]) || a[0].localeCompare(b[0]));
    const rows = userRepos.map(([name, perm]) =>
      `<tr data-go-kind="repo" data-go-id="${esc(name)}">
        <td>${repoNameCell(name)}</td>
        <td>${permPill(perm)}</td>
      </tr>`).join('');
    const maintCount = u.teams.filter(x => x.role === 'maintainer').length;

    detail.innerHTML = `<div class="detail">
      ${detailHead({ title: login, gh: ghUrl('user', login), avatar: avatarUrl(login, 104), round: true,
        sub: `${u.teams.length} team${u.teams.length===1?'':'s'}${maintCount?` (${maintCount} as maintainer)`:''} &middot; ${userRepos.length} repo${userRepos.length===1?'':'s'}` })}
      <div class="section">
        <div class="label"><span>Teams</span> <span class="n">${u.teams.length}</span></div>
        <div class="chips">${teamChips || '<span class="empty">none</span>'}</div>
      </div>
      <div class="section">
        <div class="label">${I.repo}<span>Repos (effective via teams)</span> <span class="n">${userRepos.length}</span></div>
        <table class="repo-table">
          <thead><tr><th>Repo</th><th>Best permission</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="2" class="empty">none</td></tr>'}</tbody>
        </table>
      </div>
    </div>`;
  }

  function renderRepoDetail(name) {
    const r = repoIndex[name];
    if (!r) return renderOverview();
    const maintainerOf = new Set();
    const userPerm = {};
    for (const ta of r.teams) {
      const t = teamBySlug[ta.slug];
      for (const m of ((t && memberList(t)) || [])) {
        const cur = userPerm[m.login];
        if (cur == null || permRank(ta.permission) > permRank(cur)) userPerm[m.login] = ta.permission;
        if (m.role === 'maintainer') maintainerOf.add(m.login);
      }
    }
    const userList = Object.entries(userPerm)
      .sort((a, b) => permRank(b[1]) - permRank(a[1]) || a[0].localeCompare(b[0]));
    const teamRows = r.teams.slice()
      .sort((a, b) => permRank(b.permission) - permRank(a.permission) || a.slug.localeCompare(b.slug))
      .map(ta => {
        const t = teamBySlug[ta.slug] || { name: ta.slug };
        const paths = ta.paths.map(p => `<span class="path">${esc(p)}</span>`).join('');
        return `<tr data-go-kind="team" data-go-id="${esc(ta.slug)}">
          <td><a class="r-name" data-go-kind="team" data-go-id="${esc(ta.slug)}">${esc(t.name)}</a></td>
          <td>${permPill(ta.permission)}</td>
          <td><div class="paths">${paths}</div></td>
        </tr>`;
      }).join('');
    const memberRows = userList.map(([login, perm]) =>
      `<div class="member" data-go-kind="user" data-go-id="${esc(login)}" title="${esc(perm)}">
        <img loading="lazy" src="${esc(avatarUrl(login, 36))}" alt="">
        <span class="m-name">${esc(login)}</span>${maintainerOf.has(login) ? roleBadge('maintainer') : ''}
      </div>`).join('');

    detail.innerHTML = `<div class="detail">
      ${detailHead({ title: shortRepo(name), gh: ghUrl('repo', name), icon: r.archived ? I.archive : I.repo,
        sub: `${esc(name)} &middot; ${r.teams.length} team grant${r.teams.length===1?'':'s'} &middot; ${userList.length} effective member${userList.length===1?'':'s'} &middot; best access ${permPill(r.bestPerm || 'pull')}${r.archived ? ' &middot; ' + archiveTag : ''}` })}
      <div class="section">
        <div class="label">${I.people}<span>Teams with access</span> <span class="n">${r.teams.length}</span></div>
        <table class="repo-table">
          <thead><tr><th>Team</th><th>Permission</th><th>CODEOWNERS paths</th></tr></thead>
          <tbody>${teamRows || '<tr><td colspan="3" class="empty">none</td></tr>'}</tbody>
        </table>
      </div>
      <div class="section">
        <div class="label">${I.people}<span>Effective members</span> <span class="n">${userList.length}</span></div>
        <div class="members">${memberRows || '<span class="empty">none</span>'}</div>
      </div>
    </div>`;
  }

  // ---------- View / list management ----------
  function setActiveSwitcher(v) {
    document.querySelectorAll('.view-switcher button').forEach(b =>
      b.classList.toggle('active', b.dataset.view === v));
  }
  function showList(view) {
    document.body.classList.remove('chart-mode');
    listView = view;
    for (const v of Object.keys(panes)) panes[v].hidden = (v !== view);
    archiveToggle.hidden = (view !== 'repos');
    setActiveSwitcher(view);
    applyFilter();
  }
  function kindToList(kind) { return kind === 'user' ? 'users' : kind === 'repo' ? 'repos' : 'teams'; }

  function highlightRow(kind, id) {
    document.querySelectorAll('.tree-row.selected').forEach(el => el.classList.remove('selected'));
    const row = panes[listView].querySelector(
      `.tree-row[data-kind="${CSS.escape(kind)}"][data-id="${CSS.escape(id)}"]`);
    if (row) { row.classList.add('selected'); row.scrollIntoView({ block: 'nearest' }); }
  }

  // ---------- Routing (URL hash = shareable deep link) ----------
  function hashFor(route) {
    if (route.kind) return `#${route.kind}/${encodeURIComponent(route.id)}`;
    return route.view === 'overview' ? '#' : `#${route.view}`;
  }
  function navigate(route) {
    const h = hashFor(route);
    if (location.hash === h || (h === '#' && location.hash === '')) applyRoute();
    else location.hash = h;   // triggers hashchange -> applyRoute
  }
  function parseHash() {
    const raw = (location.hash || '').replace(/^#/, '');
    if (!raw) return { view: 'overview' };
    const slash = raw.indexOf('/');
    if (slash === -1) {
      return ['teams','users','repos','chart','overview'].includes(raw) ? { view: raw } : { view: 'overview' };
    }
    return { kind: raw.slice(0, slash), id: decodeURIComponent(raw.slice(slash + 1)) };
  }
  function applyRoute() {
    const r = parseHash();
    if (r.kind) {
      mode = 'entity';
      showList(kindToList(r.kind));
      highlightRow(r.kind, r.id);
      if (r.kind === 'team') renderTeamDetail(r.id);
      else if (r.kind === 'user') renderUserDetail(r.id);
      else if (r.kind === 'repo') renderRepoDetail(r.id);
      return;
    }
    if (r.view === 'chart') {
      mode = 'chart';
      setActiveSwitcher('chart');
      document.body.classList.add('chart-mode');
      renderChart();
      return;
    }
    // overview / teams / users / repos: a list view with the overview detail
    mode = 'overview';
    showList(r.view === 'overview' ? listView : r.view);
    if (r.view !== 'overview') setActiveSwitcher(r.view);
    document.querySelectorAll('.tree-row.selected').forEach(el => el.classList.remove('selected'));
    renderOverview();
  }
  window.addEventListener('hashchange', applyRoute);

  // ---------- Filtering ----------
  function matchesTeam(t, q) {
    if (!q) return true;
    return [t.name, t.description || '', ...(t.repos || []).map(r => r.name), ...memberLogins(t)]
      .join(' ').toLowerCase().includes(q);
  }
  function applyFilter() {
    const q = filterEl.value.trim().toLowerCase();
    if (listView === 'teams') {
      const keep = new Set();
      for (const t of data.teams) if (matchesTeam(t, q)) {
        let cur = t.slug;
        while (cur) { keep.add(cur); cur = (teamBySlug[cur] || {}).parent; }
      }
      panes.teams.querySelectorAll('.tree-row').forEach(row =>
        row.classList.toggle('hide', q !== '' && !keep.has(row.dataset.id)));
    } else if (listView === 'users') {
      panes.users.querySelectorAll('.tree-row').forEach(row => {
        const u = userIndex[row.dataset.id];
        const extra = u ? [...u.teams.map(x => (teamBySlug[x.slug] || {}).name || x.slug),
          ...Object.keys(u.repos)].join(' ').toLowerCase() : '';
        row.classList.toggle('hide', q !== '' && !row.dataset.id.toLowerCase().includes(q) && !extra.includes(q));
      });
    } else if (listView === 'repos') {
      const hideArch = hideArchivedEl.checked;
      panes.repos.querySelectorAll('.tree-row').forEach(row => {
        const r = repoIndex[row.dataset.id];
        const extra = r ? r.teams.map(t => t.slug + ' ' + t.permission).join(' ').toLowerCase() : '';
        const textMiss = q !== '' && !row.dataset.id.toLowerCase().includes(q) && !extra.includes(q);
        const archMiss = hideArch && r && r.archived;
        row.classList.toggle('hide', textMiss || archMiss);
      });
    }
  }
  filterEl.addEventListener('input', applyFilter);
  hideArchivedEl.addEventListener('change', applyFilter);

  // ---------- Keyboard ----------
  function visibleRows() {
    return Array.from(panes[listView].querySelectorAll('.tree-row'))
      .filter(r => !r.classList.contains('hide') && r.offsetParent !== null);
  }
  function moveSelection(delta) {
    if (mode === 'chart') return;
    const rows = visibleRows();
    if (!rows.length) return;
    const cur = rows.findIndex(r => r.classList.contains('selected'));
    const next = rows[Math.max(0, Math.min(rows.length - 1, cur < 0 ? 0 : cur + delta))];
    if (next) navigate({ kind: next.dataset.kind, id: next.dataset.id });
  }
  document.addEventListener('keydown', e => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
    if (e.key === '/' && !typing) { e.preventDefault(); filterEl.focus(); filterEl.select(); return; }
    if (e.key === 'Escape') {
      if (typing) { document.activeElement.blur(); }
      if (filterEl.value) { filterEl.value = ''; applyFilter(); }
      return;
    }
    if (typing) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); moveSelection(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); moveSelection(-1); }
  });

  // ---------- Events ----------
  document.addEventListener('click', e => {
    if (e.target.closest('[data-ext]')) return;            // external link: let it open
    const toggleEl = e.target.closest('[data-toggle="collapse"]');
    if (toggleEl) {
      e.preventDefault(); e.stopPropagation();
      const li = toggleEl.closest('li');
      if (li && li.querySelector(':scope > ul'))
        li.dataset.collapsed = li.dataset.collapsed === 'true' ? 'false' : 'true';
      return;
    }
    const chartAct = e.target.closest('[data-chart-action]');
    if (chartAct) { if (chartAct.dataset.chartAction === 'toggle-all') setAllCollapsed(!chartCollapsed); return; }
    if (e.target.closest('#home')) { e.preventDefault(); navigate({ view: 'overview' }); return; }
    const switchBtn = e.target.closest('.view-switcher button');
    if (switchBtn) { navigate({ view: switchBtn.dataset.view }); return; }
    const goEl = e.target.closest('[data-go-kind]');
    if (goEl) { e.preventDefault(); navigate({ kind: goEl.dataset.goKind, id: goEl.dataset.goId }); return; }
    const row = e.target.closest('.tree-row');
    if (row) { navigate({ kind: row.dataset.kind || 'team', id: row.dataset.id || row.dataset.slug }); return; }
  });

  // ---------- Boot ----------
  applyRoute();
})();
</script>
</body>
</html>
"""


def render_tree(data: dict) -> str:
    """Build the left-pane indented teams tree (server-side HTML)."""
    teams = data["teams"]
    by_slug = {t["slug"]: t for t in teams}
    children: dict[str, list[dict]] = {}
    roots: list[dict] = []
    for t in teams:
        parent = t.get("parent")
        if parent and parent in by_slug:
            children.setdefault(parent, []).append(t)
        else:
            roots.append(t)
    roots.sort(key=lambda t: t["name"].lower())
    for kids in children.values():
        kids.sort(key=lambda t: t["name"].lower())

    people_icon = (
        '<svg width="14" height="14" viewBox="0 0 16 16"><path d="M2 5.5a3.5 3.5 0 1 1 5.898 '
        '2.549 5.508 5.508 0 0 1 3.034 4.084.75.75 0 1 1-1.482.235 4 4 0 0 0-7.9 0 .75.75 0 0 '
        '1-1.482-.236A5.507 5.507 0 0 1 3.102 8.05 3.493 3.493 0 0 1 2 5.5ZM11 4a3.001 3.001 0 0 '
        '1 2.22 5.018 5.01 5.01 0 0 1 2.56 3.012.749.749 0 0 1-.885.954.752.752 0 0 '
        '1-.549-.514 3.507 3.507 0 0 0-2.522-2.372.75.75 0 0 1-.574-.73v-.352a.75.75 0 0 1 '
        '.416-.672A1.5 1.5 0 0 0 11 5.5.75.75 0 0 1 11 4Zm-5.5-.5a2 2 0 1 0-.001 3.999A2 2 0 0 0 '
        '5.5 3.5Z"/></svg>'
    )
    repo_icon = (
        '<svg width="13" height="13" viewBox="0 0 16 16"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a'
        '.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0'
        '-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 '
        '1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3'
        '.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"/></svg>'
    )

    def metric(icon: str, n: int, label: str) -> str:
        zero = "" if n else " zero"
        return f'<span class="metric{zero}" title="{n} {label}">{icon}{n}</span>'

    def node(t: dict) -> str:
        kids = children.get(t["slug"], [])
        chev = "&#9662;" if kids else "&nbsp;"
        counts = (
            f'<span class="counts">{metric(people_icon, len(t["members"]), "member(s)")}'
            f'{metric(repo_icon, len(t["repos"]), "repo(s)")}</span>'
        )
        row = (
            f'<div class="tree-row" data-kind="team" data-id="{html_escape(t["slug"])}">'
            f'<span class="chev">{chev}</span>'
            f'<span class="ic">{people_icon}</span>'
            f'<span class="name">{html_escape(t["name"])}</span>'
            f'<span class="desc">{html_escape(t.get("description") or "")}</span>'
            f'<span class="spacer"></span>'
            f'<a class="ext" href="https://github.com/orgs/{html_escape(data["org"])}/teams/'
            f'{html_escape(t["slug"])}" target="_blank" rel="noopener" title="Open on GitHub" '
            f'data-ext>{_EXT_ICON}</a>'
            f'{counts}'
            f"</div>"
        )
        if kids:
            inner = "".join(node(c) for c in kids)
            row += f'<div class="tree-children"><div class="tree-connector"></div>{inner}</div>'
        return row

    return "".join(node(r) for r in roots)


_EXT_ICON = (
    '<svg width="12" height="12" viewBox="0 0 16 16"><path d="M3.75 2h3.5a.75.75 0 0 1 0 '
    '1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 '
    '0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 '
    '2Zm6.854-1h4.146a.25.25 0 0 1 .25.25v4.146a.25.25 0 0 1-.427.177L13.03 4.03 9.28 7.78a.751.751 '
    '0 0 1-1.06-1.06l3.75-3.75-1.543-1.543A.25.25 0 0 1 10.604 1Z"/></svg>'
)


def render(data: dict) -> str:
    out = HTML_TEMPLATE
    out = out.replace("__CSS__", CSS)
    out = out.replace("__ORG__", html_escape(data["org"]))
    out = out.replace("__TS__", html_escape(data.get("collected_at", "")))
    out = out.replace("__TREE__", render_tree(data))
    out = out.replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
    return out


def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: render.py <org-org.json>", file=sys.stderr)
        return 2
    in_path = pathlib.Path(argv[1])
    data = json.loads(in_path.read_text())
    if in_path.name.endswith("-org.json"):
        out_path = in_path.with_name(in_path.name[: -len("-org.json")] + "-org.html")
    else:
        out_path = in_path.with_suffix(".html")
    out_path.write_text(render(data))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
