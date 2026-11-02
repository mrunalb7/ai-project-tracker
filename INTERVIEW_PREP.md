# Interview Prep: Recruiter's Playbook for this Role

The JD is an **operations + AI-fluency** role, not an ML-research role. Recruiters here screen for judgement, communication, organisation and responsible AI use, and the project is your evidence.

## 1. Your 30-second pitch
"I built an AI project tracker that does what this role does day to day: it tracks initiatives, flags risks, drafts status reports and change comms, and turns meeting notes into action items. The part I'm proudest of is the safety design: names and emails are masked before anything reaches the AI, every output is an editable draft, and every extracted action item is checked against the source notes. I also kept a log of where the AI got things wrong."

## 2. Resume bullets (edit numbers to your real, tested results)
- Built an AI-assisted project tracker (Python, pandas, Streamlit, Claude API) that flags overdue/blocked tasks and drafts weekly status reports, cutting reporting time from ~40 to ~5 minutes on a 12-task sample.
- Designed a privacy layer that masks names, emails and phone numbers before AI processing, and a verification step that checks each extracted action item against its source quote.
- Kept an AI review log documenting errors found and fixes applied, and wrote automated tests for masking, risk logic and validation.

## 3. Questions to expect (and how to answer)

**"Tell me about a time AI got something wrong."** → Use your review log. Structure: *task → what I asked → what it got wrong → how I caught it → what I changed.* (Fill in 3 real examples by using the app: e.g. it assigned an owner who wasn't named; it gave a due date for "Wednesday" without a date; it called a blocked task "delayed".)

**"How do you handle confidential information?"** → Mask before sharing, share the minimum, use approved tools only, never paste client data into public tools, and ask when unsure.

**"How do you manage competing priorities?"** → Show the Risk flags: I rank by Blocked > Overdue > Due soon, then priority, and communicate trade-offs to the owner.

**"Why should we trust AI output?"** → We don't blindly: drafts, source quotes, numbers cross-checked against the dashboard, and a human sign-off.

**"What would you improve?"** → Calendar integration, Power BI export, feedback loop from the review log into better prompts.

**"Explain a limitation."** → Fallback extractor is simple; AI can misread informal notes; only tested on fictional data.

## 4. Behavioural stories to prepare (STAR format)
Pick real moments for: teamwork, handling a mistake, taking feedback, learning a tool fast, juggling deadlines. Tie each to a line in "What Sets You Apart" in the JD (active listening, accepting feedback, intellectual curiosity).

## 5. Your 4-step practice plan (before applying)
1. Run the app on the sample data and on one tracker you create yourself.
2. Add at least **3 real entries** to the AI Review Log tab and export it.
3. Record a 2-minute screen demo (dashboard → status report → meeting notes → review log).
4. Push to GitHub with screenshots in the README, then link it in your resume and application.

## 6. AI review log: starter template
| Output | What was wrong | How I checked | Fix |
|---|---|---|---|
| Action items | (e.g. invented an owner) | Compared to the source quote | Prompt now says "null if not explicit" |
| Status report | (e.g. wrong overdue count) | Cross-checked with dashboard | Numbers now passed in as JSON |
| Change comms | (e.g. made up a date) | Read line by line | Use [placeholders] |
