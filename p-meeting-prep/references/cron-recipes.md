# Scheduling Recipes

Two ways to run `/p-meeting-prep` on a schedule. Both must inherit credentials for `gh`, `gws`, the Slack MCP server, and the Fireflies MCP server (or those sources will be marked unavailable).

## Option A — Claude Code `/schedule`

```text
/schedule add --name meeting-prep --cron "0 7 * * 1-5" --tz "Asia/Tokyo" -- /p-meeting-prep
```

This runs the slash command weekdays at 07:00 JST and writes briefs to `{output_dir}/YYYY-MM-DD/`.

## Option B — macOS `launchd`

Save as `~/Library/LaunchAgents/tech.tailor.meeting-prep.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>           <string>tech.tailor.meeting-prep</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>-lc</string>
    <string>claude --resume --once "/p-meeting-prep"</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>StandardOutPath</key> <string>/tmp/meeting-prep.out</string>
  <key>StandardErrorPath</key> <string>/tmp/meeting-prep.err</string>
</dict>
</plist>
```

Load with `launchctl load ~/Library/LaunchAgents/tech.tailor.meeting-prep.plist`.

Verify `claude --resume --once` is the correct invocation for your Claude Code install; adjust if your version uses a different non-interactive flag (run `claude --help`).
