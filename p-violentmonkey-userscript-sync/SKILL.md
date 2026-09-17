---
name: p-violentmonkey-userscript-sync
license: MIT
description: >
  Edit a Violentmonkey userscript through its cloud sync folder (Dropbox,
  OneDrive, Google Drive) so the change actually reaches the browser. Use when adding a keybinding, shortcut, or fix to
  an existing userscript, or when a userscript edit "didn't apply" / "wasn't
  updated" after syncing. Triggers: "Violentmonkey", "userscript", "user script",
  "Tampermonkey script in Dropbox", "add a shortcut to my userscript",
  "ユーザースクリプトに追加", "反映されない".
argument-hint: "<script name> <change to make>"
compatibility: Requires Violentmonkey with cloud sync enabled, python3, and node (for syntax checking)
metadata:
  author: jackchuka
  scope: personal
  layer: workflow
  confirms:
    - overwrite the synced userscript file
---

# Violentmonkey Userscript Sync

Violentmonkey's cloud sync folder holds the editable copy of every userscript.
Editing the code there is only half the job.

`vmscript.py` locates the folder itself: `--dir` wins, then `$VM_SYNC_DIR`, then
the known Dropbox / OneDrive / Google Drive layouts. Never hard-code the path —
if detection fails the script says so and lists what it tried.

## The failure mode

Violentmonkey decides what to pull by comparing timestamps, not content. If you
change a script's `code` but leave the timestamps alone, the browser sees "no
change", keeps its own copy, and **pushes the old code back over your edit** on
the next sync. Nothing errors; the change just silently disappears.

A successful edit must bump all three:

| Where | Field | Value |
| --- | --- | --- |
| `vm@2-<key>` | `props.lastUpdated` | now (ms) |
| `Violentmonkey` (index) | `info.<key>.modified` | same now |
| `Violentmonkey` (index) | `timestamp` | now + 1 |

`scripts/vmscript.py put` does all three. Use it rather than hand-editing JSON.

## Folder layout

- `Violentmonkey` — index: `{timestamp, info: {<key>: {modified, position, enabled, deleted}}}`
- `vm@2-<key>` — one script: `{version, custom, config, props, code}`
- `<key>` encodes `namespace\nname\n` with `-XX` hex escapes (`-20` space, `-0a` newline, `-3a` colon)

Both are compact JSON. Preserve that: `json.dump(..., ensure_ascii=False, separators=(",", ":"))`.

## Workflow

```sh
S=scripts/vmscript.py            # in this skill directory

$S list                          # find the script
$S get "Quick Actions" -o /tmp/s.js
# edit /tmp/s.js — bump @version, update @description if the UX changed
$S put "Quick Actions" /tmp/s.js # syntax-checks, writes, bumps timestamps
```

Then tell the user to sync: **Violentmonkey → Settings → Sync → Sync now**.

## Common mistakes

| Mistake | Consequence |
| --- | --- |
| Editing `code` only | Edit is silently reverted on next sync |
| Pretty-printing the JSON | Diff noise; Violentmonkey rewrites it anyway |
| Skipping `node --check` | Broken script fails silently in the page |
| Changing `@name` | The sync key is derived from `namespace\nname`, so a rename orphans the old entry as `deleted: true` and loses its position/enabled state. Document new shortcuts in `@description` instead. |
| Assuming the sync is instant | Violentmonkey talks to the cloud provider's API, so the local sync client must finish uploading first |

## Fallback

If sync still doesn't land (conflict, upload lag), paste directly: `pbcopy < /tmp/s.js`,
then in Violentmonkey open the script editor, select all, paste, save. That writes
the browser's copy directly and wins the next comparison.
