#!/usr/bin/env python3
"""Read and write Violentmonkey userscripts in the cloud sync folder.

Writing a script also bumps the sync timestamps, without which Violentmonkey
treats the remote copy as unchanged and pushes its own stale copy back.
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

INDEX = "Violentmonkey"
PREFIX = "vm@2-"
ENV_VAR = "VM_SYNC_DIR"

# Violentmonkey can sync to Dropbox, OneDrive, Google Drive or WebDAV, and each
# client puts its root in a different place. Globs are expanded, first hit wins.
CANDIDATES = (
    "~/Dropbox/Apps/Violentmonkey",
    "~/Dropbox (*)/Apps/Violentmonkey",
    "~/Library/CloudStorage/Dropbox*/Apps/Violentmonkey",
    "~/OneDrive/Apps/Violentmonkey",
    "~/Library/CloudStorage/OneDrive*/Apps/Violentmonkey",
    "~/Google Drive/*/Violentmonkey",
    "~/Library/CloudStorage/GoogleDrive-*/*/Violentmonkey",
    "~/Violentmonkey",
)


def is_sync_dir(path):
    return os.path.isfile(os.path.join(path, INDEX))


def find_sync_dir(explicit=None):
    """--dir wins, then $VM_SYNC_DIR, then the known cloud-client locations."""
    for source, raw in (("--dir", explicit), (f"${ENV_VAR}", os.environ.get(ENV_VAR))):
        if raw:
            path = os.path.expanduser(raw)
            if not is_sync_dir(path):
                sys.exit(f"{source}={raw!r} has no {INDEX} index file")
            return path

    for pattern in CANDIDATES:
        for path in sorted(glob.glob(os.path.expanduser(pattern))):
            if is_sync_dir(path):
                return path

    sys.exit(
        "no Violentmonkey sync folder found. Set "
        f"{ENV_VAR} or pass --dir. Looked in:\n  " + "\n  ".join(CANDIDATES)
    )


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def decode(key):
    """Turn Violentmonkey's -XX hex escapes back into readable text."""
    out, i = [], 0
    while i < len(key):
        if key[i] == "-" and i + 2 < len(key):
            try:
                out.append(chr(int(key[i + 1 : i + 3], 16)))
                i += 3
                continue
            except ValueError:
                pass
        out.append(key[i])
        i += 1
    return " / ".join(part for part in "".join(out).split("\n") if part.strip())


def entries(root):
    index = load(os.path.join(root, INDEX))
    return index, {k: v for k, v in index["info"].items() if not v.get("deleted")}


def resolve(root, query):
    _, live = entries(root)
    hits = [k for k in live if query.lower() in decode(k).lower() or query.lower() in k.lower()]
    if not hits:
        sys.exit(f"no script matches {query!r}. Run `vmscript.py list`.")
    if len(hits) > 1:
        sys.exit("ambiguous query, matches:\n  " + "\n  ".join(decode(k) for k in hits))
    return hits[0]


def cmd_list(args):
    _, live = entries(args.dir)
    for key, meta in sorted(live.items(), key=lambda kv: kv[1].get("position", 0)):
        state = "on " if meta.get("enabled") else "off"
        print(f"{state}  {decode(key)}")


def cmd_get(args):
    key = resolve(args.dir, args.query)
    code = load(os.path.join(args.dir, PREFIX + key))["code"]
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(code)
        print(args.out)
    else:
        sys.stdout.write(code)


def syntax_check(code):
    """Refuse to write code that node can't parse. No-op when node is missing."""
    node = shutil.which("node")
    if not node:
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "check.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        proc = subprocess.run(  # noqa: S603 - fixed argv, node resolved via which
            [node, "--check", path], capture_output=True, text=True
        )
    if proc.returncode != 0:
        sys.exit(f"syntax error, nothing written:\n{proc.stderr.strip()}")


def cmd_put(args):
    key = resolve(args.dir, args.query)
    with open(args.file, encoding="utf-8") as f:
        code = f.read()

    if not args.no_check:
        syntax_check(code)

    now = int(time.time() * 1000)
    script_path = os.path.join(args.dir, PREFIX + key)
    index_path = os.path.join(args.dir, INDEX)

    script = load(script_path)
    script["code"] = code
    script.setdefault("props", {})["lastUpdated"] = now
    save(script_path, script)

    index = load(index_path)
    index["info"][key]["modified"] = now
    index["timestamp"] = now + 1
    save(index_path, index)

    print(f"wrote {decode(key)} @ {now} ({time.ctime(now / 1000)})")
    print("now sync in Violentmonkey: Settings -> Sync -> Sync now")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--dir",
        help=f"Violentmonkey sync folder (default: ${ENV_VAR}, else auto-detected)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list synced scripts").set_defaults(func=cmd_list)

    g = sub.add_parser("get", help="print or save a script's code")
    g.add_argument("query")
    g.add_argument("-o", "--out", help="write code to this file instead of stdout")
    g.set_defaults(func=cmd_get)

    u = sub.add_parser("put", help="write code back and bump sync timestamps")
    u.add_argument("query")
    u.add_argument("file")
    u.add_argument("--no-check", action="store_true", help="skip node --check")
    u.set_defaults(func=cmd_put)

    args = p.parse_args()
    args.dir = find_sync_dir(args.dir)
    args.func(args)


if __name__ == "__main__":
    main()
