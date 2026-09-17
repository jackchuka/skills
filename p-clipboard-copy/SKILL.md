---
name: p-clipboard-copy
license: MIT
description: >
  Pull copy-worthy fragments out of the ongoing session — commands, code blocks,
  file paths, URLs, IDs, queries, message drafts, error snippets, diffs — and push
  them into the macOS clipboard history as separate entries, stripped of markdown
  fences, shell prompts and line numbers, ordered so the most relevant one is what
  Cmd+V pastes. Message drafts are copied as rich text so bold and bullet lists
  survive pasting into Slack. Use when the user says "copy that", "clip this",
  "copy the command and the path", "put those on my clipboard", "clip the last few
  things", or "/p-clipboard-copy".
argument-hint: "[hint] [--all] [--yes] [--delay SEC]"
compatibility: >
  macOS only; requires pbcopy, osascript and textutil. Calibrated for Raycast
  Clipboard History, which polls the pasteboard about every 0.5s. Other clipboard
  managers may need a different --delay.
metadata:
  author: jackchuka
  scope: personal
  layer: primitive
  confirms:
    - overwrite the current system clipboard
---

# Clipboard Copy

Copy several useful fragments from this session into clipboard history at once,
each as its own entry, each containing only the part worth pasting.

The user has a clipboard history manager, so copying 3-6 items is cheap and
useful. The value of this skill is **extraction quality**, not volume: a command
without its `$` prompt, a path without the prose around it, a query without the
explanation. Never copy a whole assistant message — that is what the built-in
`/copy` is for.

## Arguments

- **`[hint]`** — free text narrowing what to grab: `/p-clipboard-copy the sql and the pod name`.
  With no hint, auto-detect from the recent turns.
- **`--all`** — widen the scan from the last few turns to the whole session.
- **`--yes`** — skip the confirmation step and copy immediately.
- **`--delay SEC`** — seconds between copies. Default `0.7`.

## Scan window

Default: the last ~3 assistant turns plus any user turn that named something
concrete. With `--all`, the whole session. If a hint names something older than
the window, search the whole session for it regardless.

## Workflow

### 1. Collect candidates

Walk the scan window and pull out every fragment that matches the taxonomy
below. A candidate is one clipboard entry — never bundle two unrelated things
into one entry, and never split something that is only useful whole (a
multi-line command with `&&` is one entry).

Drop anything that is:

- Already trivially retypable (`ls`, `cd ..`, a single digit).
- Prose or explanation rather than an artifact.
- A near-duplicate of another candidate — keep the most complete version.
- Secret material: tokens, passwords, private keys, `.env` values. Skip these
  silently unless the user's hint asked for them by name.

### 2. Rank, then propose

Rank by how likely the user is to paste it *next*. Signals, strongest first:

1. The hint named it.
2. It is the thing the last turn was actually about — the command just written,
   the URL just created.
3. It is an action the user must now take elsewhere (run this, open this, paste
   this into a PR).
4. It is an identifier they will need to reference again.

Prefer ranking a formatted `draft` #1 when it is a close call. Any entry can
carry formatting, but only the top-ranked one pastes rich on a plain Cmd+V —
the rest need an extra action when recalled from history (see below).

Print a numbered table, ranked most relevant first:

| # | Type | Preview | Size |
|---|------|---------|------|
| 1 | draft (rich) | `*Shipped this week* — 3 bullets` | 412 B |
| 2 | url | `https://github.com/org/repo/pull/42` | 36 B |
| 3 | path | `src/handler/auth.go:118` | 24 B |

Truncate previews to ~60 chars. Then stop and ask:

> Copy all 3? (`ok` / `just 1,3` / `drop 2` / `also <thing>`)

Wait for the answer. Skip this step only with `--yes`.

### 3. Copy

Write each selected fragment to its own file in the scratchpad directory, named
`NN-<type>.txt`, then hand them to the script **in reverse relevance order** —
least relevant first, most relevant last — so the top-ranked item is the active
clipboard and the rest stack behind it in history:

```sh
scripts/clip.sh /scratch/03-path.txt /scratch/02-url.txt /scratch/01-command.txt
```

For a formatted draft, also write a sibling `NN-draft.html` next to its `.txt`.
The script picks it up automatically — no flag, and it works for any number of
entries:

```sh
# 01-draft.html sits beside 01-draft.txt and is detected
scripts/clip.sh /scratch/03-path.txt /scratch/02-url.txt /scratch/01-draft.txt
```

Always pass files, never inline strings — inline text gets mangled by shell
quoting on anything containing quotes, backticks, `$`, or newlines.

Then report where each item landed in the history:

```
Clipboard history (Cmd+V pastes #1):
  1. draft  rich — bold and bullets paste formatted
  2. url    https://github.com/org/repo/pull/42
  3. path   src/handler/auth.go:118
```

When an entry below #1 is rich, add one line: recall it in Raycast, then
Cmd+K -> "Paste as... RTF" to keep the formatting.

## Detection taxonomy

| Type | What lands on the clipboard |
|------|------------------------------|
| `command` | The bare command. No `$`/`%`/`>` prompt, no fence, no trailing comment, no surrounding explanation. |
| `code` | The block body only, original indentation preserved, no fence and no language tag. |
| `path` | Absolute path, or `path:line` when a specific line was cited. Repo-relative only if the user was working relative. |
| `url` | The bare URL. No markdown link syntax, no trailing punctuation from the sentence. |
| `id` | Commit SHA, branch name, PR/issue number, pod or container name, resource ID, ticket key. |
| `draft` | Commit message, PR body, Slack message, email text. Plain text, plus an HTML flavor when it has formatting — see below. |
| `query` | SQL, GraphQL, `jq` expression, BigQuery statement — the query alone. |
| `error` | The log or stack trace lines themselves, no commentary. |
| `diff` | Patch text that would apply cleanly with `git apply`. |

## Extraction rules

These are the "only the necessary part" rules. Apply all of them:

- **Strip fences.** Remove ```` ``` ```` delimiters and the language tag.
- **Strip prompts.** Leading `$ `, `% `, `> `, `# ` on shell lines.
- **Strip line numbers.** Output from `cat -n`, `grep -n`, or a `Read` tool result
  carries `   12→` or `12:` prefixes — remove them and restore original indentation.
- **Strip ANSI escapes** from captured terminal output.
- **Strip markdown link syntax** — `[text](url)` becomes the URL when the candidate
  is a url, the text when it is a draft.
- **No trailing newline** on single-line values (paths, URLs, IDs) so pasting into
  a form field or another shell does not submit early.
- **Keep the trailing newline** on multi-line blocks (code, diffs, drafts).
- **Never truncate the payload.** Previews are truncated; clipboard entries are not.

## Rich text for drafts

Slack's composer converts Markdown **as you type**, never on paste. Pasted
`*bold*` and `**bold**` both show literal asterisks, and `- item` stays a dash.
The only thing that pastes as real formatting is a rich flavor on the pasteboard.

To make an entry rich, write a sibling `.html` file next to its `.txt`. The
script detects it and puts three flavors on the pasteboard: plain text, HTML and
RTF (converted from the HTML with `textutil`).

**Any number of entries can be rich**, but they do not behave identically:

| Entry | How it pastes formatted |
|-------|-------------------------|
| Rank #1 (the live clipboard) | Cmd+V — renders rich straight away, no extra step |
| Anything recalled from history | Cmd+K -> "Paste as... RTF" in Raycast |

Plain Enter on a history entry pastes the plain-text flavor, and "Paste as...
HTML" does not render — RTF is the flavor that survives the round trip. This was
verified on this machine, not assumed.

Write the HTML as a fragment with no `<html>`/`<body>` wrapper. Escape `&`, `<`
and `>` in the content itself. All of these are verified to render in Slack:

| Markdown | HTML to emit |
|----------|--------------|
| `**bold**` | `<b>bold</b>` |
| `*italic*` / `_italic_` | `<i>italic</i>` |
| `~~strike~~` | `<s>strike</s>` |
| `` `code` `` | `<code>code</code>` |
| ```` ```block``` ```` | `<pre>block</pre>` |
| `[text](url)` | `<a href="url">text</a>` |
| `> quote` | `<blockquote>quote</blockquote>` |
| `- item` | `<ul><li>item</li></ul>` |
| nested `- item` | nested `<ul>` inside the parent `<li>` — renders correctly |
| `1. item` | `<ol><li>item</li></ol>` |
| line break | `<br>` |
| `# Heading` | `<b>Heading</b><br>` — Slack has no heading element |

Emit a heading as exactly `<b>text</b><br>`. The script keys off that shape and
inserts a break before each such heading in **both** flavors, so Cmd+V and
"Paste as... RTF" render identically. Without it a heading sits flush against the
list or paragraph above it. Inline bold mid-sentence is never followed by `<br>`,
so it is left alone, and a heading at the very start gets no leading blank line.

The RTF conversion passes `-inputencoding UTF-8`. Without it `textutil` falls
back to the system codepage and mangles every non-ASCII character — em dashes,
`•` bullets, accented letters, kana all arrive as mojibake.

The plain-text file is still required: it is the fallback anywhere rich text is
not accepted, and what plain Enter pastes from history. Make it readable rather
than marked up — drop emphasis markers, use `•` for bullets, indent nested
bullets four spaces, and render links as `text (url)`.

## Notes

- **Why 0.7s.** Raycast polls the pasteboard roughly every 0.5s. Measured on this
  machine: copies spaced 1.2s and 0.7s apart are all captured; copies spaced 0.3s
  apart are overwritten before the poll and lost, leaving only the last one. 0.7 is
  the calibrated floor with margin. Raising item count costs `(N-1) x 0.7s`.
- **No trailing sleep is needed** — the final item stays on the pasteboard and gets
  picked up by the next poll whatever happens.
- **The user's current clipboard is overwritten**, but it is already in their history,
  so nothing is lost.
- **Other clipboard managers**: Maccy and Paste also poll. If entries go missing,
  raise `--delay`.
