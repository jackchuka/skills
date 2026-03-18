# Agent: Gather Calendar Activity (Previous Business Day)

```bash
gws calendar events list --params '{"calendarId":"primary","timeMin":"PREV_DATE_RFC3339","timeMax":"TODAY_DATE_RFC3339","singleEvents":true,"orderBy":"startTime"}'
```

**Note:** Do NOT use `gws calendar +agenda` here — it only shows **future** events. Use `events list` with explicit `timeMin`/`timeMax` for past dates.

**Filtering rules:**
- Extract meeting names/titles
- Skip declined events
- Skip all-day events unless they look like work items

**Error handling:**
- If `gws` is not installed or fails, skip gracefully and note "Calendar data unavailable"

**Context variables:**
- `PREV_DATE_RFC3339` — previous business day in RFC3339 format (e.g. `2024-01-15T00:00:00Z`)
- `TODAY_DATE_RFC3339` — today's date in RFC3339 format (e.g. `2024-01-16T00:00:00Z`)
