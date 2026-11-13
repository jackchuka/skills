# README Guide

Target: a README that sells the tool in the first screen. A reader should see what it does, that it is maintained, and what it looks like running, before scrolling.

## Layout

````markdown
<div align="center">

# <name>

**<one-line promise: the outcome for the user, not the mechanism>**

<one or two lines on how it does it; use <br> to balance line lengths>

[![Test](https://github.com/<owner>/<repo>/actions/workflows/test.yml/badge.svg)](https://github.com/<owner>/<repo>/actions/workflows/test.yml)
[![Release](https://img.shields.io/github/v/release/<owner>/<repo>?sort=semver)](https://github.com/<owner>/<repo>/releases)
[![Go Version](https://img.shields.io/github/go-mod/go-version/<owner>/<repo>)](go.mod)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

<img src="assets/demo.gif" alt="<what the demo shows, as a sentence>" width="800">

[Installation](#installation) · [Quick Start](#quick-start) · [<key section>](#...) · [Limits](#limits)

</div>

---

<Problem paragraph: why existing tools/approaches fall short.>

**<name>** <what it does about it, in user terms>.

## Features

- **<Bold lead>** — <one-line explanation>
...

## Installation
## Quick Start        (command + real output in a ```text block)
## <Reference sections: output/flags/config tables>
## Limits             (what it does not do; honest scope)
## Related            (sibling tools, how they differ)
## License
````

Badges: only those that resolve. Drop Release until the first tag exists; swap Go Version for the language's equivalent (npm version, PyPI version). Libraries add a pkg.go.dev badge.

## Demo GIF (CLI / TUI tools)

Record with [vhs](https://github.com/charmbracelet/vhs) so the GIF is reproducible and regenerated whenever output changes. Commit both `assets/demo.tape` and `assets/demo.gif`.

### Offline fake data

Never record against real accounts: the GIF would leak private org/repo/user names and drift over time. Instead, run the real CLI against a fake backend:

- `assets/demo/main.go` — a tiny `main` that wires the real command (`cmd.Execute` or equivalent) to a fake implementation of the API client interface, returning a fabricated org (`acme`, users `alice`/`bob`).
- If the code has no injectable interface for the client, add one; it also helps tests.
- For `gh` extensions, shadow `gh` with a shell function in the hidden setup so the tape types the real command: `gh() { shift; "$D/demo" "$@"; }`.

### Tape template

```tape
# Regenerate with: vhs assets/demo.tape (from the repository root)

Output assets/demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1400
Set Height 400
Set Padding 24
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms

Hide
Type `export D=/tmp/<name>-demo && rm -rf "$D" && mkdir -p "$D" && go build -o "$D/demo" ./assets/demo && cd "$D" && export PS1='\[\e[1;35m\]$ \[\e[0m\]' && clear`
Enter
Sleep 5s
Show

Type "<name> <main use case>"
Sleep 400ms
Enter
Sleep 5s

Type "clear"
Enter
Type "<name> <second use case: a flag that shows off a key feature>"
Sleep 400ms
Enter
Sleep 5s
```

Guidelines:
- 2-4 scenes telling a story (basic run → refine with a flag → alternate output format). Keep it under ~30s.
- Size `Height` to the output so there is no empty space or scrolling; check each frame.
- Keep the GIF under ~1 MB.
- Make sure `go build ./...` and the linter accept `assets/demo` (or exclude it explicitly).
- After recording, open the GIF (Read tool) and verify every scene rendered as intended.

### Non-CLI projects

- Libraries: no GIF; put a short, runnable code example right under the badges instead.
- Web/GUI apps: a screenshot or short screen recording in `assets/`.
