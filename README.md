# GenAI Training Program — Quiz Dashboard

A Streamlit app for the 5-day GenAI training program: one continuous storytelling journey through 5 chapters (10 questions each — 3 easy / 3 medium / 4 hard), automatic scoring, a trophy/celebration finale, and a leaderboard backed by Google Sheets.

There's no login. The entry screen just asks for an email and a display name — email is the unique key so two participants can both type "Dave" and still show up as separate rows on the leaderboard. No password, no verification.

## How it works

The flow is linear and automatic — participants never pick a chapter or topic themselves:

1. **Entry** — email + display name.
2. **Intro** — a roadmap preview of the 5 chapters ahead.
3. **Chapters 1–5** — 10 questions each, click-to-answer (no separate submit button), auto-advancing question to question.
4. **Chapter recap** — after chapters 1–4, a short results beat (score, tier, answer review) before continuing to the next chapter.
5. **Celebration** — after chapter 5, a trophy screen with confetti, total score, tier badge, and a per-chapter breakdown — with the leaderboard rendered immediately underneath, no extra click needed.

The leaderboard is also reachable any time from the sidebar once a participant has finished their run.


## using Google cloud project -> Google sheets for storing the results
## deployed in streamlit community from the github repo

##  Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

If secrets aren't filled in yet, the entry screen shows an error and stops — that's expected, it means step 1 isn't finished. Once secrets are correct, the entry form appears and quiz attempts land as rows in your Sheet's "Leaderboard" tab.



## Files

| File | Purpose |
|---|---|
| `app.py` | The Streamlit app |
| `questions.json` | 50 questions (5 topics × 10), with options and answers |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Keeps `secrets.toml` and local junk out of git |
| `secrets.toml.example` | Template for `.streamlit/secrets.toml` |
