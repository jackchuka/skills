# agent-gather-calendar-report

Match calendar fetch to report date range:

```bash
# default (today) — +agenda only looks forward
gws calendar +agenda --today

# --yesterday or past dates — use raw API with timeMin/timeMax
gws calendar events list --params '{"calendarId":"primary","timeMin":"YESTERDAY_RFC3339","timeMax":"TODAY_RFC3339","singleEvents":true,"orderBy":"startTime"}'

# --days N (past N days)
gws calendar events list --params '{"calendarId":"primary","timeMin":"N_DAYS_AGO_RFC3339","timeMax":"NOW_RFC3339","singleEvents":true,"orderBy":"startTime"}'
```

**Note:** `gws calendar +agenda` only shows **future** events. For past dates, use `events list` with explicit `timeMin`/`timeMax`.

## Filtering Rules

| Keep                    | Drop                           |
| ----------------------- | ------------------------------ |
| 1:1s, reviews, planning | Duplicate standups (keep one)  |
| External meetings       | Declined/canceled              |
| Decision meetings       | Routine syncs without outcomes |
| Interviews, demos       | All-day FYI events             |
