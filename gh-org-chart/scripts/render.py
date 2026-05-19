#!/usr/bin/env python3
"""Render an HTML org explorer from a collect.sh JSON file.

Three views are exposed in the same single-file HTML:
  - Teams: hierarchical tree (default).
  - Users: flat list of every member across teams.
  - Repos: flat list of every repo seen across teams.
The detail pane cross-links between the three.
"""

import json
import pathlib
import sys

CSS = """
:root {
  --bg: #f5f5f7; --panel: #ffffff; --border: #d1d1d6;
  --text: #1d1d1f; --muted: #86868b; --accent: #0071e3;
  --selected-bg: #e8f4fd; --pill-bg: transparent;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1d1d1f; --panel: #2d2d2f; --border: #424245;
    --text: #f5f5f7; --muted: #86868b; --accent: #0a84ff;
    --selected-bg: rgba(10,132,255,0.15);
  }
}
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, system-ui, sans-serif;
  background: var(--bg); color: var(--text); }
header { padding: 12px 20px; border-bottom: 1px solid var(--border);
  background: var(--panel); display: flex; gap: 12px; align-items: center; }
header h1 { margin: 0; font-size: 16px; }
header .ts { color: var(--muted); font-size: 12px; }
main { display: grid; grid-template-columns: 30% 70%; min-height: calc(100vh - 50px); }
@media (max-width: 900px) { main { grid-template-columns: 1fr; } }
body.chart-mode main { grid-template-columns: 1fr; }
body.chart-mode #tree { display: none; }
#tree, #detail { padding: 12px; overflow: auto; }
#tree { border-right: 1px solid var(--border); background: var(--panel); }
#detail .empty { color: var(--muted); }

.view-switcher { display: flex; gap: 4px; margin-left: auto;
  background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 3px; }
.view-switcher button { padding: 5px 12px; font-size: 12px; font-weight: 600;
  background: transparent; color: var(--muted); border: none; border-radius: 5px;
  cursor: pointer; font-family: inherit; }
.view-switcher button:hover { color: var(--text); }
.view-switcher button.active { background: var(--panel); color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.view-pane[hidden] { display: none; }

.tree-row { display: flex; align-items: center; gap: 8px; padding: 6px;
  border-radius: 6px; cursor: pointer; }
.tree-row:hover { background: var(--selected-bg); }
.tree-row.selected { background: var(--selected-bg); border: 1px solid var(--accent); padding: 5px; }
.tree-row .chev { width: 12px; color: var(--muted); font-size: 10px; }
.tree-row .icon { font-size: 13px; }
.tree-row .avatar { width: 20px; height: 20px; border-radius: 50%; background: var(--border); flex-shrink: 0; }
.tree-row .name { font-weight: 600; }
.tree-row .desc { color: var(--muted); font-size: 11px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0; }
.tree-row .pill { color: var(--muted); font-size: 11px;
  padding: 1px 6px; border: 1px solid var(--border); border-radius: 10px; }
.tree-children { position: relative; padding-left: 18px; margin-top: 2px; }
.tree-connector { position: absolute; left: 11px; top: 0; bottom: 0;
  width: 1px; background: var(--border); }
.tree-children.collapsed { display: none; }
"""

CSS += """
.detail h2 { margin: 0 0 4px; }
.detail h2 a { color: inherit; text-decoration: none; }
.detail h2 a:hover { color: var(--accent); }
.detail .desc { color: var(--muted); margin-bottom: 16px; }
.detail .section { margin-bottom: 20px; }
.detail .label { text-transform: uppercase; font-size: 11px; color: var(--muted);
  letter-spacing: 0.05em; margin-bottom: 8px; }
.detail .head { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.detail .head img { width: 48px; height: 48px; border-radius: 50%; background: var(--border); }
.members { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 6px; }
.member { display: flex; align-items: center; gap: 8px; padding: 4px 6px;
  border-radius: 6px; cursor: pointer; }
.member:hover { background: var(--selected-bg); }
.member img { width: 28px; height: 28px; border-radius: 50%; background: var(--border); flex-shrink: 0; }
.member span { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.repo-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.repo-table th, .repo-table td { text-align: left; padding: 6px 8px;
  border-bottom: 1px solid var(--border); vertical-align: top; }
.repo-table th { color: var(--muted); font-weight: 500; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.05em; }
.repo-table a { color: var(--accent); text-decoration: none; cursor: pointer; }
.repo-table a:hover { text-decoration: underline; }
.repo-table .perm { font-family: ui-monospace, monospace; font-size: 11px;
  padding: 1px 6px; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; }
.paths { display: flex; flex-wrap: wrap; gap: 4px; }
.path { font-family: ui-monospace, monospace; font-size: 11px;
  padding: 2px 6px; background: var(--bg); border: 1px solid var(--border);
  border-radius: 4px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { padding: 3px 10px; background: var(--bg); border: 1px solid var(--border);
  border-radius: 12px; font-size: 12px; cursor: pointer; color: var(--text);
  text-decoration: none; display: inline-block; }
.chip:hover { border-color: var(--accent); color: var(--accent); }
.subteams a { color: var(--accent); text-decoration: none; margin-right: 12px; cursor: pointer; }
"""

CSS += """
.filter-bar { position: sticky; top: 0; background: var(--panel);
  padding: 4px 0 10px; border-bottom: 1px solid var(--border); margin-bottom: 8px;
  display: flex; align-items: center; gap: 8px; z-index: 1; }
.filter-bar input { flex: 1; padding: 6px 10px; border: 1px solid var(--border);
  border-radius: 6px; background: var(--bg); color: var(--text); font-size: 12px; }
.tree-row.dim { opacity: 0.35; }
.tree-row.hide { display: none; }

.org-chart { padding: 8px 4px 24px; font-size: 13px; }
.org-chart .legend { color: var(--muted); font-size: 12px; margin-bottom: 12px; }
.chart-toolbar { display: flex; gap: 8px; margin-bottom: 12px; align-items: center;
  position: sticky; top: 0; background: var(--bg); padding: 6px 0; z-index: 1; }
.chart-toolbar input { flex: 1; max-width: 360px; padding: 6px 10px;
  border: 1px solid var(--border); border-radius: 6px; background: var(--panel);
  color: var(--text); font-size: 12px; }
.chart-toolbar button { padding: 5px 12px; font-size: 12px; font-weight: 600;
  background: var(--panel); border: 1px solid var(--border); border-radius: 6px;
  cursor: pointer; color: var(--text); }
.chart-toolbar button:hover { border-color: var(--accent); color: var(--accent); }
.chart-toolbar .stat { color: var(--muted); font-size: 12px; }
.h-tree, .h-tree ul { list-style: none; margin: 0; padding: 0; position: relative; }
.h-tree ul { padding-left: 28px; }
.h-tree li { position: relative; padding: 3px 0 3px 22px; line-height: 1.5; }
.h-tree > li { padding-left: 0; }
.h-tree ul > li::before {
  content: ""; position: absolute; left: 0; top: 0; height: 0.95em;
  width: 18px; border-left: 1px solid var(--border); border-bottom: 1px solid var(--border);
  border-bottom-left-radius: 6px;
}
.h-tree ul > li::after {
  content: ""; position: absolute; left: 0; top: 0.95em; bottom: 0;
  border-left: 1px solid var(--border);
}
.h-tree ul > li:last-child::after { display: none; }
.h-node { display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px;
  border-radius: 6px; cursor: pointer; border: 1px solid transparent; }
.h-node:hover { background: var(--selected-bg); border-color: var(--accent); }
.h-node.team { font-weight: 600; }
.h-node.user img { width: 18px; height: 18px; border-radius: 50%; }
.h-node .count { color: var(--muted); font-size: 11px; font-weight: 400; margin-left: 4px; }
.h-node.org { background: var(--bg); border: 1px solid var(--border); }
.h-node .chev { color: var(--muted); font-size: 9px; width: 10px; text-align: center;
  display: inline-block; transition: transform 0.12s; cursor: pointer;
  padding: 2px; margin: -2px 2px -2px -2px; border-radius: 3px; }
.h-node .chev:hover { background: var(--bg); color: var(--text); }
.h-tree li[data-collapsed="true"] > ul { display: none; }
.h-tree li[data-collapsed="true"] > .h-node .chev { transform: rotate(-90deg); }
.h-tree li.hide { display: none; }
.h-node.highlight { background: var(--selected-bg); border-color: var(--accent); }
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>__ORG__ — org chart</title>
  <style>__CSS__</style>
</head>
<body>
<header>
  <h1>__ORG__</h1>
  <span class="ts">collected __TS__</span>
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
      <span aria-hidden="true">&#128269;</span>
      <input id="filter" type="search" placeholder="Filter...">
    </div>
    <div id="view-teams" class="view-pane">__TREE__</div>
    <div id="view-users" class="view-pane" hidden></div>
    <div id="view-repos" class="view-pane" hidden></div>
  </aside>
  <section id="detail"><p class="empty">Pick an entry on the left.</p></section>
</main>
<script type="application/json" id="data">__DATA__</script>
<script>
(function() {
  const data = JSON.parse(document.getElementById('data').textContent);
  const teamBySlug = Object.fromEntries(data.teams.map(t => [t.slug, t]));
  const teamChildren = {};
  for (const t of data.teams) {
    if (t.parent) (teamChildren[t.parent] = teamChildren[t.parent] || []).push(t);
  }

  const PERM_ORDER = { pull: 0, triage: 1, push: 2, maintain: 3, admin: 4 };
  function permRank(p) { return PERM_ORDER[p] == null ? -1 : PERM_ORDER[p]; }

  // Build user index: login -> { login, teams: [slug], repos: { repoName: bestPerm } }
  const userIndex = {};
  for (const t of data.teams) {
    for (const login of (t.members || [])) {
      const u = userIndex[login] || (userIndex[login] = { login, teams: [], repos: {} });
      if (!u.teams.includes(t.slug)) u.teams.push(t.slug);
      for (const r of (t.repos || [])) {
        const cur = u.repos[r.name];
        if (cur == null || permRank(r.permission) > permRank(cur)) {
          u.repos[r.name] = r.permission;
        }
      }
    }
  }
  const users = Object.values(userIndex).sort((a, b) =>
    a.login.toLowerCase().localeCompare(b.login.toLowerCase()));

  // Build repo index: name -> { name, teams: [{slug, permission, paths}], bestPerm }
  const repoIndex = {};
  for (const t of data.teams) {
    for (const r of (t.repos || [])) {
      const ri = repoIndex[r.name] || (repoIndex[r.name] = { name: r.name, teams: [], bestPerm: null });
      ri.teams.push({ slug: t.slug, permission: r.permission, paths: r.codeowner_paths || [] });
      if (ri.bestPerm == null || permRank(r.permission) > permRank(ri.bestPerm)) {
        ri.bestPerm = r.permission;
      }
    }
  }
  const repos = Object.values(repoIndex).sort((a, b) =>
    a.name.toLowerCase().localeCompare(b.name.toLowerCase()));

  // Roots for the chart = teams with no parent (or whose parent is missing).
  const teamRoots = data.teams.filter(t => !t.parent || !teamBySlug[t.parent])
    .sort((a, b) => a.name.localeCompare(b.name));

  const detail = document.getElementById('detail');
  const filterEl = document.getElementById('filter');
  const panes = {
    teams: document.getElementById('view-teams'),
    users: document.getElementById('view-users'),
    repos: document.getElementById('view-repos'),
  };
  let currentView = 'teams';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;');
  }

  function avatarUrl(login, size) {
    return `https://github.com/${encodeURIComponent(login)}.png?size=${size || 40}`;
  }

  // ---------- Tree rendering for users & repos (teams tree is server-rendered) ----------
  function renderUsersTree() {
    panes.users.innerHTML = users.map(u =>
      `<div class="tree-row" data-kind="user" data-id="${esc(u.login)}">
        <img class="avatar" loading="lazy" src="${esc(avatarUrl(u.login, 24))}" alt="">
        <span class="name">${esc(u.login)}</span>
        <span class="desc"></span>
        <span class="pill">${u.teams.length} &middot; ${Object.keys(u.repos).length}</span>
      </div>`
    ).join('');
  }

  function renderReposTree() {
    panes.repos.innerHTML = repos.map(r => {
      const short = r.name.includes('/') ? r.name.split('/').slice(1).join('/') : r.name;
      return `<div class="tree-row" data-kind="repo" data-id="${esc(r.name)}">
        <span class="icon">&#128193;</span>
        <span class="name">${esc(short)}</span>
        <span class="desc">${esc(r.bestPerm || '')}</span>
        <span class="pill">${r.teams.length}</span>
      </div>`;
    }).join('');
  }

  renderUsersTree();
  renderReposTree();

  // ---------- Chart (at-a-glance, indented tree) ----------
  let chartCollapsed = false;
  // GitHub inherits subteam membership upward — a parent team's .members list contains
  // everyone in its descendant teams. For the chart we want only "direct" members:
  // those not in any descendant team.
  function descendantMembers(slug) {
    const set = new Set();
    const stack = [...(teamChildren[slug] || [])];
    while (stack.length) {
      const c = stack.pop();
      for (const m of (c.members || [])) set.add(m);
      for (const cc of (teamChildren[c.slug] || [])) stack.push(cc);
    }
    return set;
  }
  function renderChartTeam(t) {
    const inherited = descendantMembers(t.slug);
    const direct = (t.members || []).filter(m => !inherited.has(m));
    const members = direct.slice()
      .sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))
      .map(login => `<li><span class="h-node user" data-go-kind="user" data-go-id="${esc(login)}">
        <img loading="lazy" src="${esc(avatarUrl(login, 24))}" alt="">${esc(login)}
      </span></li>`).join('');
    const subs = (teamChildren[t.slug] || []).slice()
      .sort((a, b) => a.name.localeCompare(b.name))
      .map(c => `<li>${renderChartTeam(c)}</li>`).join('');
    const hasChildren = !!(members || subs);
    const inner = hasChildren ? `<ul>${members}${subs}</ul>` : '';
    const chev = hasChildren
      ? `<span class="chev" data-toggle="collapse">&#9662;</span>`
      : '';
    const total = (t.members || []).length;
    const countLabel = direct.length === total ? `${total}` : `${direct.length}/${total}`;
    return `<span class="h-node team" data-go-kind="team" data-go-id="${esc(t.slug)}">
      ${chev}${esc(t.name)}<span class="count" title="direct/total members">${countLabel} &middot; ${(t.repos || []).length}</span>
    </span>${inner}`;
  }
  function renderChart() {
    const roots = teamRoots.map(t => `<li>${renderChartTeam(t)}</li>`).join('');
    detail.innerHTML = `<div class="org-chart">
      <div class="chart-toolbar">
        <input id="chart-filter" type="search" placeholder="Filter teams, members...">
        <button data-chart-action="toggle-all">${chartCollapsed ? 'Expand all' : 'Collapse all'}</button>
        <span class="stat" id="chart-stat"></span>
      </div>
      <div class="legend">${data.teams.length} teams &middot; tree shows every team a person belongs to (no deduplication)</div>
      <ul class="h-tree">
        <li><span class="h-node org"><span class="chev" data-toggle="collapse">&#9662;</span>${esc(data.org)}</span>
          <ul>${roots}</ul>
        </li>
      </ul>
    </div>`;
    // Wire up the chart-local filter.
    const f = document.getElementById('chart-filter');
    if (f) f.addEventListener('input', () => applyChartFilter(f.value));
    if (chartCollapsed) setAllCollapsed(true);
  }

  function setAllCollapsed(collapsed) {
    const chart = detail.querySelector('.org-chart');
    if (!chart) return;
    chart.querySelectorAll('li').forEach(li => {
      // Only mark li's that actually have a child ul (i.e. expandable teams).
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
    lis.forEach(li => { li.classList.remove('hide'); });
    chart.querySelectorAll('.h-node.highlight').forEach(n => n.classList.remove('highlight'));
    const stat = document.getElementById('chart-stat');
    if (!q) { if (stat) stat.textContent = ''; return; }
    // Expand everything so matches inside collapsed branches become visible.
    chart.querySelectorAll('li[data-collapsed="true"]').forEach(li => li.dataset.collapsed = 'false');
    // Determine which li's match by their own node's text (excluding descendants).
    const matched = new Set();
    lis.forEach(li => {
      const node = li.querySelector(':scope > .h-node');
      if (!node) return;
      // Use the node's own text (not nested ul); since the ul is a sibling of the
      // h-node within li, textContent of the h-node itself is safe.
      if (node.textContent.toLowerCase().includes(q)) {
        matched.add(li);
        node.classList.add('highlight');
      }
    });
    const visible = new Set();
    matched.forEach(li => {
      visible.add(li);
      // Show all descendants of a matched team.
      li.querySelectorAll('li').forEach(d => visible.add(d));
      // Show ancestors.
      let p = li.parentElement;
      while (p && p !== chart) {
        if (p.tagName === 'LI') visible.add(p);
        p = p.parentElement;
      }
    });
    lis.forEach(li => { if (!visible.has(li)) li.classList.add('hide'); });
    if (stat) stat.textContent = `${matched.size} match${matched.size === 1 ? '' : 'es'}`;
  }

  // ---------- View switching ----------
  function switchView(view) {
    document.querySelectorAll('.view-switcher button').forEach(b =>
      b.classList.toggle('active', b.dataset.view === view));
    if (view === 'chart') {
      currentView = view;
      document.body.classList.add('chart-mode');
      renderChart();
      return;
    }
    if (!panes[view]) return;
    document.body.classList.remove('chart-mode');
    currentView = view;
    for (const v of Object.keys(panes)) panes[v].hidden = (v !== view);
    applyFilter();
  }

  // ---------- Detail rendering ----------
  function renderDetail(kind, id) {
    if (kind === 'team') return renderTeamDetail(id);
    if (kind === 'user') return renderUserDetail(id);
    if (kind === 'repo') return renderRepoDetail(id);
    detail.innerHTML = '<p class="empty">Pick an entry on the left.</p>';
  }

  function teamLink(slug) {
    const t = teamBySlug[slug];
    if (!t) return esc(slug);
    return `<a class="chip" data-go-kind="team" data-go-id="${esc(slug)}">${esc(t.name)}</a>`;
  }
  function userLink(login) {
    return `<div class="member" data-go-kind="user" data-go-id="${esc(login)}">
      <img loading="lazy" src="${esc(avatarUrl(login, 36))}" alt="">
      <span>${esc(login)}</span>
    </div>`;
  }
  function repoLink(name) {
    return `<a data-go-kind="repo" data-go-id="${esc(name)}">${esc(name)}</a>`;
  }

  function renderTeamDetail(slug) {
    const t = teamBySlug[slug];
    if (!t) { detail.innerHTML = '<p class="empty">Unknown team.</p>'; return; }
    const breadcrumb = t.parent && teamBySlug[t.parent]
      ? `<div class="desc"><a data-go-kind="team" data-go-id="${esc(t.parent)}">&larr; ${esc(teamBySlug[t.parent].name)}</a></div>`
      : '';
    const members = (t.members || []).map(userLink).join('');
    const rows = (t.repos || []).map(r => {
      const paths = (r.codeowner_paths || []).map(p => `<span class="path">${esc(p)}</span>`).join('');
      return `<tr>
        <td>${repoLink(r.name)}</td>
        <td><span class="perm">${esc(r.permission)}</span></td>
        <td><div class="paths">${paths}</div></td>
      </tr>`;
    }).join('');
    const subteams = (teamChildren[t.slug] || []).map(c =>
      `<a data-go-kind="team" data-go-id="${esc(c.slug)}">${esc(c.name)}</a>`
    ).join('');

    detail.innerHTML = `
      <div class="detail">
        ${breadcrumb}
        <h2><a href="https://github.com/orgs/${esc(data.org)}/teams/${esc(t.slug)}" target="_blank" rel="noopener">${esc(t.name)}</a></h2>
        <p class="desc">${esc(t.description || '')}</p>
        <div class="section">
          <div class="label">Members (${(t.members||[]).length})</div>
          <div class="members">${members || '<span class="empty">none</span>'}</div>
        </div>
        <div class="section">
          <div class="label">Repos (${(t.repos||[]).length})</div>
          <table class="repo-table">
            <thead><tr><th>Repo</th><th>Permission</th><th>CODEOWNERS paths</th></tr></thead>
            <tbody>${rows || '<tr><td colspan="3" class="empty">none</td></tr>'}</tbody>
          </table>
        </div>
        ${subteams ? `<div class="section subteams"><div class="label">Subteams</div>${subteams}</div>` : ''}
      </div>`;
  }

  function renderUserDetail(login) {
    const u = userIndex[login];
    if (!u) { detail.innerHTML = '<p class="empty">Unknown user.</p>'; return; }
    const teamChips = u.teams.map(teamLink).join(' ');
    const userRepos = Object.entries(u.repos)
      .sort((a, b) => permRank(b[1]) - permRank(a[1]) || a[0].localeCompare(b[0]));
    const rows = userRepos.map(([name, perm]) => `<tr>
      <td>${repoLink(name)}</td>
      <td><span class="perm">${esc(perm)}</span></td>
    </tr>`).join('');

    detail.innerHTML = `
      <div class="detail">
        <div class="head">
          <img loading="lazy" src="${esc(avatarUrl(login, 96))}" alt="">
          <div>
            <h2><a href="https://github.com/${esc(login)}" target="_blank" rel="noopener">${esc(login)}</a></h2>
            <p class="desc">${u.teams.length} team(s) &middot; ${userRepos.length} repo(s)</p>
          </div>
        </div>
        <div class="section">
          <div class="label">Teams</div>
          <div class="chips">${teamChips || '<span class="empty">none</span>'}</div>
        </div>
        <div class="section">
          <div class="label">Repos (effective via team membership)</div>
          <table class="repo-table">
            <thead><tr><th>Repo</th><th>Best permission</th></tr></thead>
            <tbody>${rows || '<tr><td colspan="2" class="empty">none</td></tr>'}</tbody>
          </table>
        </div>
      </div>`;
  }

  function renderRepoDetail(name) {
    const r = repoIndex[name];
    if (!r) { detail.innerHTML = '<p class="empty">Unknown repo.</p>'; return; }
    // Aggregate unique users who have access via any team.
    const userPerm = {}; // login -> best perm
    for (const ta of r.teams) {
      const t = teamBySlug[ta.slug];
      for (const login of ((t && t.members) || [])) {
        const cur = userPerm[login];
        if (cur == null || permRank(ta.permission) > permRank(cur)) userPerm[login] = ta.permission;
      }
    }
    const userList = Object.entries(userPerm)
      .sort((a, b) => permRank(b[1]) - permRank(a[1]) || a[0].localeCompare(b[0]));

    const teamRows = r.teams
      .slice()
      .sort((a, b) => permRank(b.permission) - permRank(a.permission) || a.slug.localeCompare(b.slug))
      .map(ta => {
        const t = teamBySlug[ta.slug] || { name: ta.slug };
        const paths = ta.paths.map(p => `<span class="path">${esc(p)}</span>`).join('');
        return `<tr>
          <td><a data-go-kind="team" data-go-id="${esc(ta.slug)}">${esc(t.name)}</a></td>
          <td><span class="perm">${esc(ta.permission)}</span></td>
          <td><div class="paths">${paths}</div></td>
        </tr>`;
      }).join('');

    const memberRows = userList.map(([login, perm]) =>
      `<div class="member" data-go-kind="user" data-go-id="${esc(login)}" title="${esc(perm)}">
        <img loading="lazy" src="${esc(avatarUrl(login, 36))}" alt="">
        <span>${esc(login)}</span>
      </div>`
    ).join('');

    detail.innerHTML = `
      <div class="detail">
        <h2><a href="https://github.com/${esc(name)}" target="_blank" rel="noopener">${esc(name)}</a></h2>
        <p class="desc">${r.teams.length} team grant(s) &middot; ${userList.length} effective member(s) &middot; best access: ${esc(r.bestPerm || '')}</p>
        <div class="section">
          <div class="label">Teams with access</div>
          <table class="repo-table">
            <thead><tr><th>Team</th><th>Permission</th><th>CODEOWNERS paths</th></tr></thead>
            <tbody>${teamRows || '<tr><td colspan="3" class="empty">none</td></tr>'}</tbody>
          </table>
        </div>
        <div class="section">
          <div class="label">Effective members (${userList.length})</div>
          <div class="members">${memberRows || '<span class="empty">none</span>'}</div>
        </div>
      </div>`;
  }

  // ---------- Selection ----------
  function select(kind, id) {
    if (currentView !== kindToView(kind)) switchView(kindToView(kind));
    document.querySelectorAll('.tree-row.selected').forEach(el => el.classList.remove('selected'));
    const row = panes[currentView].querySelector(
      `.tree-row[data-kind="${CSS.escape(kind)}"][data-id="${CSS.escape(id)}"]`);
    if (row) {
      row.classList.add('selected');
      row.scrollIntoView({ block: 'nearest' });
    }
    renderDetail(kind, id);
  }
  function kindToView(kind) {
    return kind === 'user' ? 'users' : kind === 'repo' ? 'repos' : 'teams';
  }

  // ---------- Filtering ----------
  function matchesTeam(t, q) {
    if (!q) return true;
    const hay = [t.name, t.description || '',
      ...(t.repos || []).map(r => r.name),
      ...(t.members || [])].join(' ').toLowerCase();
    return hay.includes(q);
  }
  function applyFilter() {
    const q = filterEl.value.trim().toLowerCase();
    if (currentView === 'teams') {
      const keep = new Set();
      for (const t of data.teams) {
        if (matchesTeam(t, q)) {
          let cur = t.slug;
          while (cur) { keep.add(cur); cur = (teamBySlug[cur] || {}).parent; }
        }
      }
      panes.teams.querySelectorAll('.tree-row').forEach(row => {
        row.classList.toggle('hide', q !== '' && !keep.has(row.dataset.id));
      });
    } else if (currentView === 'users') {
      panes.users.querySelectorAll('.tree-row').forEach(row => {
        const login = row.dataset.id.toLowerCase();
        const u = userIndex[row.dataset.id];
        const extra = u ? [
          ...u.teams.map(s => (teamBySlug[s] || {}).name || s),
          ...Object.keys(u.repos),
        ].join(' ').toLowerCase() : '';
        row.classList.toggle('hide', q !== '' && !login.includes(q) && !extra.includes(q));
      });
    } else if (currentView === 'repos') {
      panes.repos.querySelectorAll('.tree-row').forEach(row => {
        const name = row.dataset.id.toLowerCase();
        const r = repoIndex[row.dataset.id];
        const extra = r ? r.teams.map(t => t.slug + ' ' + t.permission).join(' ').toLowerCase() : '';
        row.classList.toggle('hide', q !== '' && !name.includes(q) && !extra.includes(q));
      });
    }
  }
  filterEl.addEventListener('input', applyFilter);

  // ---------- Events ----------
  document.addEventListener('click', e => {
    const toggleEl = e.target.closest('[data-toggle="collapse"]');
    if (toggleEl) {
      e.preventDefault(); e.stopPropagation();
      const li = toggleEl.closest('li');
      if (li && li.querySelector(':scope > ul')) {
        li.dataset.collapsed = li.dataset.collapsed === 'true' ? 'false' : 'true';
      }
      return;
    }
    const chartAct = e.target.closest('[data-chart-action]');
    if (chartAct) {
      if (chartAct.dataset.chartAction === 'toggle-all') setAllCollapsed(!chartCollapsed);
      return;
    }
    const switchBtn = e.target.closest('.view-switcher button');
    if (switchBtn) { switchView(switchBtn.dataset.view); return; }
    const goEl = e.target.closest('[data-go-kind]');
    if (goEl) { e.preventDefault(); select(goEl.dataset.goKind, goEl.dataset.goId); return; }
    const row = e.target.closest('.tree-row');
    if (row) {
      const kind = row.dataset.kind || 'team';
      const id = row.dataset.id || row.dataset.slug;
      select(kind, id);
      return;
    }
  });
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

    def node(t: dict) -> str:
        kids = children.get(t["slug"], [])
        chev = "&#9662;" if kids else "&nbsp;"
        pill = f"{len(t['repos'])} &middot; {len(t['members'])}"
        row = (
            f'<div class="tree-row" data-kind="team" data-id="{html_escape(t["slug"])}">'
            f'<span class="chev">{chev}</span>'
            f'<span class="icon">&#128101;</span>'
            f'<span class="name">{html_escape(t["name"])}</span>'
            f'<span class="desc">{html_escape(t.get("description") or "")}</span>'
            f'<span class="pill">{pill}</span>'
            f"</div>"
        )
        if kids:
            inner = "".join(node(c) for c in kids)
            row += f'<div class="tree-children"><div class="tree-connector"></div>{inner}</div>'
        return row

    return "".join(node(r) for r in roots)


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
