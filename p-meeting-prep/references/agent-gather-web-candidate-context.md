# Agent: Gather Web Context for Interview Candidates

For `interview` meetings, run public web research on the candidate to surface background that the interviewer can use to tailor the conversation.

## When to run

- Category `interview` only.
- Skip for any other category.
- Skip if no candidate name can be parsed from the event title or description (set finding to `_(no candidate name parsed)_`).

## Candidate name extraction

Order of preference:

1. Event title pattern `… - <name>様` or `… - <name>` (e.g. `Casual Interview - 戸田 朋花様` → `戸田 朋花`).
2. Ashby briefing link's HTML title (if reachable without auth — usually not, skip on 403).
3. The first non-internal attendee's display name (where the email domain is not `{internal_domain}`).

Strip honorifics (`様`, `さん`, `Mr.`, `Ms.`).

## Query strategy

Run 2–4 web searches in parallel. Start broad, then refine. Useful query shapes:

- `"<full name>" <likely industry/role keywords>` — e.g. `"戸田 朋花" エンジニア`.
- `"<full name>" LinkedIn` / `"<full name>" GitHub` / `"<full name>" X (Twitter)`.
- `"<full name>" <company hint from event description or coordinator>` — e.g. job title from Ashby briefing.
- If the first round surfaces a specific signal (e.g. "未踏採択", "OSS maintainer", "PhD"), fan out one more query to deepen it.

For Japanese candidates, run both `"<姓 名>"` and `"<姓名>"` (with and without space).

## Disambiguation

If results clearly mix multiple people:

- Use the strongest unique signal in the event (coordinator email domain, role from Ashby, location) to pick the most likely person.
- If still ambiguous, return findings for the top 1–2 candidates and flag `disambiguation_needed: true`.

## Extract

Return a structured object the template can render:

- `affiliation` — current company / school, if found.
- `notable` — list of 1–3 highlights (program selections, OSS projects, talks, papers, awards). Each entry: `{summary, url}`.
- `interests` — technical interests / themes inferred from public output.
- `profiles` — list of public profile links: `{kind: github|x|linkedin|blog|other, url}`.
- `disambiguation_needed` — bool.
- `notes` — free-text caveats (e.g. "未確定: 同名異人複数").

## Failure modes

| Situation | Action |
| --------- | ------ |
| Web search tool unavailable | Return `{status: "unavailable"}`. |
| Zero useful results | Return `{status: "no-public-footprint"}`. |
| Page fetch returns 403 / paywall | Skip that source, keep the search-result snippet as the citation. |
| Time budget exceeded (15 s) | Return whatever was gathered so far and add `truncated: true`. |

## Privacy

- Only use public web sources. Do not attempt authenticated lookups (LinkedIn scraping, paid databases).
- Do not write personal data beyond what the candidate has already chosen to publish.
- Do not infer protected attributes (age, nationality, family status) even if visible.
