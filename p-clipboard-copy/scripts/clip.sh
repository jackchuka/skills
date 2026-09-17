#!/usr/bin/env bash
# Copy each file's contents to the macOS clipboard in order, pausing between
# entries so a polling clipboard manager records every one as its own item.
#
# Any entry can carry formatting: if FILE has a sibling with the same basename
# and a .html extension, that entry is copied as rich text (plain + HTML + RTF)
# instead of plain text. The HTML flavor is what Slack, Gmail and Notion read on
# a direct paste; the RTF flavor is what survives a round trip through Raycast
# clipboard history, where it is restored via "Paste as... RTF".
set -euo pipefail

DELAY="${CLIP_DELAY:-0.7}"

usage() {
  cat <<'USAGE'
usage: clip.sh [--delay SEC] FILE [FILE ...]

Copies each FILE to the clipboard in the order given, sleeping between entries.
The LAST file ends up as the active clipboard; earlier ones stack behind it in
clipboard history.

  --delay SEC   seconds between copies (default 0.7, or $CLIP_DELAY)

Rich text: if "foo.txt" has a sibling "foo.html", that entry is copied with
plain, HTML and RTF flavors. Pasting it straight from the clipboard renders
formatted; recalling it from Raycast history renders formatted via
"Paste as... RTF" (plain Enter pastes the plain-text flavor).

Raycast polls the pasteboard about every 0.5s; 0.7 is the calibrated floor.
Copies spaced 0.3s apart get overwritten before the poll and are lost.
USAGE
}

files=()
while [ $# -gt 0 ]; do
  case "$1" in
    --delay)
      [ $# -ge 2 ] || { echo "clip.sh: --delay needs a value" >&2; exit 2; }
      DELAY="$2"; shift 2 ;;
    --delay=*) DELAY="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; files+=("$@"); break ;;
    -*) echo "clip.sh: unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) files+=("$1"); shift ;;
  esac
done

if [ "${#files[@]}" -eq 0 ]; then usage >&2; exit 2; fi

command -v pbcopy >/dev/null 2>&1 || { echo "clip.sh: pbcopy not found (macOS only)" >&2; exit 1; }

for f in "${files[@]}"; do
  [ -f "$f" ] || { echo "clip.sh: no such file: $f" >&2; exit 1; }
done

hex() { hexdump -ve '1/1 "%.2x"' < "$1"; }

# Put plain, HTML and RTF flavors on the pasteboard together. pbcopy writes only
# plain text, so this goes through AppleScript. Every payload is hex-encoded,
# which sidesteps AppleScript string escaping entirely -- quotes, backslashes and
# newlines in the content are all safe.
copy_rich() {
  local plain="$1" html="$2" rtf="$3"
  if [ -n "$rtf" ]; then
    printf 'set the clipboard to {«class utf8»:«data utf8%s», «class HTML»:«data HTML%s», «class RTF »:«data RTF %s»}' \
      "$(hex "$plain")" "$(hex "$html")" "$(hex "$rtf")" | osascript - >/dev/null
  else
    printf 'set the clipboard to {«class utf8»:«data utf8%s», «class HTML»:«data HTML%s»}' \
      "$(hex "$plain")" "$(hex "$html")" | osascript - >/dev/null
  fi
}

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

total="${#files[@]}"
for i in "${!files[@]}"; do
  f="${files[$i]}"
  htmlfile="${f%.*}.html"
  note=""
  if [ "$f" != "$htmlfile" ] && [ -f "$htmlfile" ]; then
    base=$(basename "${f%.*}")
    richhtml="$tmpdir/$base.html"
    rtffile="$tmpdir/$base.rtf"
    # A heading -- <b>...</b><br>, the skill's heading convention -- otherwise
    # renders flush against the list or paragraph above it. Insert a break before
    # each one, but not before inline bold (which is never followed by <br>) and
    # not at the very start. Applied to both flavors so that Cmd+V and Raycast's
    # "Paste as... RTF" render the same entry identically.
    perl -0777 -pe 's{<b>((?:(?!</b>).)*)</b><br>}{<br><b>$1</b><br>}gs; s{^<br>}{}' \
      < "$htmlfile" > "$richhtml"
    # textutil defaults to the system codepage and mangles non-ASCII (em dashes,
    # bullet characters, accents, kana) without an explicit input encoding.
    if ! textutil -stdin -format html -inputencoding UTF-8 -convert rtf -stdout \
         < "$richhtml" > "$rtffile" 2>/dev/null; then
      rtffile=""
      note=" + html (rtf conversion failed)"
    else
      note=" + html + rtf"
    fi
    copy_rich "$f" "$richhtml" "$rtffile"
  else
    pbcopy < "$f"
  fi
  bytes=$(wc -c < "$f" | tr -d ' ')
  printf 'copied %d/%d  %-24s %s bytes%s\n' "$((i + 1))" "$total" "$(basename "$f")" "$bytes" "$note"
  if [ "$((i + 1))" -lt "$total" ]; then sleep "$DELAY"; fi
done

printf '\nactive clipboard (Cmd+V): %s\n' "$(basename "${files[$((total - 1))]}")"
