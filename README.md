# AI Project Tracker & Weekly Status Assistant

A small web app that helps a project team **track initiatives, spot risks, and draft status reports, action items and change communications with AI, safely.**

Built as a portfolio project for the *PwC Business AI Engineer – Intern 2027* role (Acceleration Center India, Internal Firm Services). It mirrors the day-to-day work in the job description: tracking and reporting on initiatives, data analysis, meeting coordination, change communications, and AI-human collaboration.

## What it does

| Feature | JD requirement it maps to |
|---|---|
| Dashboard: completion %, overdue / blocked / due-soon, workload per owner | Tracking, managing and reporting on projects; data analysis |
| Data validation (missing owners, bad dates, duplicate IDs) | Quality work, professional standards |
| AI weekly status report (editable draft) | Reporting; AI fluency |
| Meeting notes → action items, decisions, risks (JSON) | Coordinating meetings; AI-human collaboration |
| Follow-up meeting invite (.ics) | Managing schedules |
| Change communication drafts | Change management and change communications |
| Privacy masking of names / emails / phones before AI | Handling confidential information |
| Quote check on every extracted action item | Verifying AI output |
| AI review log (what the AI got wrong, how I fixed it) | AI-human collaboration, accepting feedback |

## Design principles

1. **Privacy first**: only masked text is sent to the model. You can preview exactly what it receives.
2. **No invention**: prompts forbid guessing owners, dates or numbers; unknowns return `null` / "not stated".
3. **Human in the loop**: every output is an editable *draft*, and action items carry a ✅ / ⚠️ verification flag.
4. **Works offline**: with no API key, rule-based fallbacks run so anyone can try it.

## Quick start

```bash
git clone <your-repo-url> && cd pwc-ai-tracker
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# optional, enables AI drafting:
export ANTHROPIC_API_KEY="your-key"                   # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key"
streamlit run app.py
```

Run the tests: `python test_core.py`

## Project structure

```
app.py            Streamlit UI (5 tabs)
analysis.py       Cleaning, validation, risk flags, summaries (pandas)
ai_helpers.py     Prompts, API calls, fallbacks, quote verification
privacy.py        Masking / unmasking of personal data
test_core.py      Tests for masking, risk logic, validation, verification
data/             Sample tracker + sample meeting notes (all fictional)
```

## Results on the sample data

- 12 tasks across 4 initiatives; the dashboard flags 3 overdue, 1 blocked, 2 due within 3 days, 1 stale.
- Manual status-report drafting (~30–45 min) reduced to ~5 min including review. *Replace with your own timed numbers after you test it.*

## Limitations & next steps

- Sample data is fictional; the app has not been tested on real firm data (and should go through proper approvals before it is).
- The fallback extractor is basic; the AI path is more accurate but must always be reviewed.
- Next: Teams/Outlook calendar integration, Power BI export, multi-language comms, role-based access.

