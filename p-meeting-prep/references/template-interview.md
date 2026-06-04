# Template: Interview Brief

## Header

```markdown
### HH:MM–HH:MM <Meeting title>  `[interview]`
Attendees: <interviewer names>, <candidate name>（候補者）
Meet: <link or "—">
Ashby briefing: <ashby URL if present in event description>
Related today: <cluster siblings, if any>
```

## Body sections

### Candidate

- Name (best effort from title or description).
- Role being interviewed for (from title or description, or `_(確認: Ashby briefing)_` if not derivable).
- Recruiting coordinator (organizer / creator email, if not the interviewer).

### 事前リサーチ（Internet）

Source: `agent-gather-web-candidate-context.md`. Render the structured findings as bullets, grouped by topic. Each bullet should include the source link inline.

- If the web search returned solid matches: list affiliation, notable projects / achievements (program acceptances, OSS, talks, papers), technical interests, public profiles (GitHub / X / LinkedIn / personal blog).
- If multiple candidates share the name and identity could not be disambiguated, add a leading note: `> 同名異人の可能性あり。冒頭で経歴の認識合わせを推奨。`
- If no useful public information was found: `_(public information minimal — Ashby briefing で経歴確認)_`.
- If the web tool was unavailable: `_(web search unavailable)_`.

### Prior rounds

- For each prior interview Fireflies recording: `<meeting_date> — <overview (1 line)>`.
- If none: `_(no prior rounds found)_`.
- If Fireflies unavailable: `_(unavailable)_`.

### Focus areas（こちらが探りたいこと）

- 3–5 bullets derived from the role, event description, and what stands out in the web research.
- Phrasing in `{lang}`.

### こちらからの質問（候補者用）

Concrete questions to ask, grouped into 3 short blocks (`A. 経歴・現職`, `B. 候補者固有テーマ`, `C. <Company>・キャリア`). Aim for 8–12 questions total.

- `B. 候補者固有テーマ` should be tailored from the web-research findings (e.g. their OSS project, a research theme, a recent talk). If no public background was found, replace block B with `B. これまでの取り組み` and ask open-ended portfolio questions.
- Bias toward questions that surface motivation, judgment, and trade-offs — not knowledge quizzes.
- Phrasing in `{lang}`.

### 候補者から聞かれそうな質問 / こちらの回答メモ

3–6 bullets the interviewer can glance at to answer common candidate questions:

- 1-sentence product pitch.
- Tech stack summary.
- Why the candidate's specific background maps to the company (1–2 lines, derived from web research).
- Hiring process next steps (defer details to the coordinator).
- Work style basics (location / remote / language usage).

If no web research is available, omit the third bullet.

### Open questions

- Bullets carried over from prior rounds' action items / open evaluation gaps.
- If none: `_(no questions flagged from prior rounds)_`.

### Notes

- Remind the interviewer to open the Ashby briefing pre-meeting and leave feedback after.
- Suggested time-box for a 30 min slot: 自己紹介 5 / ヒアリング 10 / 会社説明 10 / 質疑 5（lang に応じて訳）.
