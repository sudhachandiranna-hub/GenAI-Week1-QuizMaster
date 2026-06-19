# GenAI Training Program — Quiz Dashboard

A Streamlit app for the 5-day GenAI training program: one continuous storytelling journey through 5 chapters (10 questions each — 3 easy / 3 medium / 4 hard), automatic scoring, a trophy/celebration finale, and a leaderboard backed by Google Sheets.

There's no login. The entry screen just asks for an email and a display name — email is the unique key so two participants can both type "Dave" and still show up as separate rows on the leaderboard. No password, no verification.

Google Sheets is required, not optional — the app needs it to save results and won't run without it. Set that up first (step 1), then run the app.

## How it works

The flow is linear and automatic — participants never pick a chapter or topic themselves:

1. **Entry** — email + display name.
2. **Intro** — a roadmap preview of the 5 chapters ahead.
3. **Chapters 1–5** — 10 questions each, click-to-answer (no separate submit button), auto-advancing question to question.
4. **Chapter recap** — after chapters 1–4, a short results beat (score, tier, answer review) before continuing to the next chapter.
5. **Celebration** — after chapter 5, a trophy screen with confetti, total score, tier badge, and a per-chapter breakdown — with the leaderboard rendered immediately underneath, no extra click needed.

The leaderboard is also reachable any time from the sidebar once a participant has finished their run.

## 1. Set up the Google Sheets leaderboard

About 10 minutes, once.

1. **Create a Google Sheet.** Go to sheets.google.com, create a new blank sheet (any name). Copy the **sheet ID** from its URL — the long string between `/d/` and `/edit`:
   `https://docs.google.com/spreadsheets/d/`**`THIS_PART_IS_THE_ID`**`/edit`
   Leave the sheet otherwise empty — the app creates its own "Leaderboard" tab and header row on first use.

2. **Create a Google Cloud project** (or reuse one) at console.cloud.google.com.

3. **Enable two APIs** for that project: search for and enable **Google Sheets API** and **Google Drive API** (APIs & Services → Enable APIs and Services).

4. **Create a service account**: APIs & Services → Credentials → Create Credentials → Service Account. Give it any name (e.g. `quiz-leaderboard`). No roles needed — skip that step.

5. **Create a key for the service account**: open the service account → Keys tab → Add Key → Create new key → **JSON**. This downloads a `.json` file — keep it private, never commit it to GitHub.

6. **Share the Sheet with the service account.** Open the downloaded JSON, copy the `client_email` value (looks like `quiz-leaderboard@your-project.iam.gserviceaccount.com`). In your Google Sheet, click **Share** and give that email address **Editor** access.

7. **Fill in your local secrets file.** Copy the template:
   ```bash
   mkdir -p .streamlit
   cp secrets.toml.example .streamlit/secrets.toml
   ```
   Edit `.streamlit/secrets.toml`: set `sheet_id` to the ID from step 1, and copy every field from the downloaded JSON into the matching `[gcp_service_account]` key (`project_id`, `private_key_id`, `private_key`, `client_email`, `client_id`, etc.). Keep the `\n` characters inside `private_key` exactly as the JSON has them.

`.streamlit/secrets.toml` is already in `.gitignore` — it will never be committed.

## 2. Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

If secrets aren't filled in yet, the entry screen shows an error and stops — that's expected, it means step 1 isn't finished. Once secrets are correct, the entry form appears and quiz attempts land as rows in your Sheet's "Leaderboard" tab.

## 3. Publish to GitHub

```bash
git init                     # skip if already a repo
git add app.py questions.json requirements.txt .gitignore secrets.toml.example README.md
git commit -m "Add GenAI quiz dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Double check `git status` shows no `secrets.toml` or service-account JSON staged before you push.

## 4. Deploy on Streamlit Community Cloud

1. Go to share.streamlit.io and sign in with GitHub.
2. Click **New app** → pick your repo, branch (`main`), and main file path (`app.py`, or `quiz-app/app.py` if it's in a subfolder).
3. Before (or right after) deploying, open **Advanced settings → Secrets** and paste the *full contents* of your local `.streamlit/secrets.toml` (the real one with your actual keys, not the `.example` file) into the Secrets box. This is how the deployed app gets the same Google Sheets access your local run has, since the real secrets file is never pushed to GitHub.
4. Click **Deploy**. First boot takes a minute or two while it installs `requirements.txt`.
5. Anyone with the app URL can now enter their email, take quizzes, and appear on the shared leaderboard.

If you ever rotate the service-account key, update it in both `.streamlit/secrets.toml` locally and in the Cloud app's Secrets settings — they're independent copies.

## Files

| File | Purpose |
|---|---|
| `app.py` | The Streamlit app |
| `questions.json` | 50 questions (5 topics × 10), with options and answers |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Keeps `secrets.toml` and local junk out of git |
| `secrets.toml.example` | Template for `.streamlit/secrets.toml` |
