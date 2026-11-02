"""AI Project Tracker & Weekly Status Assistant - Streamlit app.

Run:  streamlit run app.py
"""
import datetime as dt
import pandas as pd
import streamlit as st

import analysis as an
import ai_helpers as ai
import privacy as pv

st.set_page_config(page_title="AI Project Tracker", page_icon="📊", layout="wide")

# ---------------- Sidebar ----------------
st.sidebar.title("📊 AI Project Tracker")
st.sidebar.caption("Tracks initiatives, drafts status reports and action items with AI - "
                   "with privacy masking and human review built in.")

uploaded = st.sidebar.file_uploader("Upload tracker (CSV / Excel)", type=["csv", "xlsx"])
use_sample = st.sidebar.checkbox("Use sample data", value=uploaded is None)
as_of = st.sidebar.date_input("Report date", value=dt.date(2026, 11, 3))

if ai.ai_available():
    st.sidebar.success("AI mode: Google Gemini connected")
else:
    st.sidebar.warning(
        "Offline mode: set GEMINI_API_KEY to enable AI drafting. "
        "Rule-based fallbacks are used meanwhile."
    )

st.sidebar.info("🔒 Names, emails and phone numbers are masked before any text is sent to the AI.")

# ---------------- Load data ----------------
if uploaded is not None:
    raw = an.load_tracker(uploaded)
elif use_sample:
    raw = an.load_tracker("data/sample_tracker.csv")
else:
    st.info("Upload a tracker or tick 'Use sample data' in the sidebar.")
    st.stop()

issues = an.validate(raw)
if issues:
    st.error("Data quality problems found - fix these first:")
    for i in issues:
        st.write(f"- {i}")
    if any("Missing required columns" in i for i in issues):
        st.stop()

df = an.enrich(raw, today=as_of)
nums = an.summary_numbers(df)
name_map = pv.build_name_map(df["Owner"].dropna().unique())

if "review_log" not in st.session_state:
    st.session_state.review_log = []

tab_dash, tab_status, tab_notes, tab_comms, tab_log = st.tabs(
    ["📈 Dashboard", "📝 Weekly Status", "🗒️ Meeting Notes → Actions", "📣 Change Comms", "✅ AI Review Log"])

# ---------------- Dashboard ----------------
with tab_dash:
    st.subheader("Initiative overview")
    c = st.columns(5)
    c[0].metric("Tasks", nums["total"])
    c[1].metric("Completed", f"{nums['completion_pct']}%")
    c[2].metric("Overdue", nums["overdue"])
    c[3].metric("Blocked", nums["blocked"])
    c[4].metric("Due in ≤3 days", nums["due_soon"])

    left, right = st.columns(2)
    with left:
        st.markdown("**Progress by initiative**")
        st.dataframe(an.by_initiative(df), hide_index=True, width="stretch")
        st.markdown("**Status mix**")
        st.bar_chart(df["Status"].value_counts())
    with right:
        st.markdown("**Open tasks per owner (workload)**")
        st.bar_chart(an.workload(df))
        st.markdown("**Risk flags**")
        st.bar_chart(df["Risk"].value_counts())

    st.markdown("**⚠️ Needs attention**")
    risky = df[df["Risk"].isin(["Overdue", "Blocked", "Due Soon", "Stale"])]
    st.dataframe(risky[["Task ID", "Initiative", "Task", "Owner", "Status", "Due Date", "Risk"]]
                 .sort_values("Due Date"), hide_index=True, width="stretch")

# ---------------- Weekly status ----------------
with tab_status:
    st.subheader("Generate weekly status report")
    a, b = st.columns(2)
    audience = a.selectbox("Audience", ["Project leadership", "Client stakeholders", "Internal team"])
    tone = b.selectbox("Tone", ["Professional", "Concise", "Friendly"])

    if st.button("Generate draft", key="gen_status"):
        rows = (df[df["Risk"].isin(["Overdue", "Blocked", "Due Soon"])]
                [["Task", "Owner", "Risk", "Due Date"]].copy())
        rows["Due Date"] = rows["Due Date"].dt.strftime("%d %b %Y")
        # PRIVACY: mask owner names before the data goes into the prompt
        rows["Owner"] = rows["Owner"].map(lambda n: name_map.get(n, n))
        rows["Task"] = rows["Task"].map(lambda t: pv.mask_text(t, name_map))
        text, mode = ai.generate_status_report(nums, rows.to_dict("records"), audience, tone)
        st.session_state.status_draft = pv.unmask_text(text, name_map)
        st.session_state.status_mode = mode

    if "status_draft" in st.session_state:
        st.caption(f"Source: {'Google Gemini' if st.session_state.status_mode == 'ai' else 'rule-based fallback'}"
                   " · DRAFT - verify every number against the dashboard before sending.")
        st.text_area("Editable draft", st.session_state.status_draft, height=280, key="status_edit")
        st.download_button("Download as .txt", st.session_state.get("status_edit", ""),
                           file_name="weekly_status.txt")

# ---------------- Meeting notes ----------------
with tab_notes:
    st.subheader("Turn meeting notes into action items")
    default_notes = open("data/sample_meeting_notes.txt").read()
    notes = st.text_area("Paste meeting notes", default_notes, height=260)

    all_names = list(name_map.keys())
    masked = pv.mask_text(notes, name_map)
    with st.expander("🔒 See exactly what the AI will receive (masked)"):
        st.code(masked)

    if st.button("Extract action items", key="extract"):
        result, mode = ai.extract_actions(masked)
        result["actions"] = ai.verify_quotes(result["actions"], masked)
        st.session_state.extract_result = result
        st.session_state.extract_mode = mode

    if "extract_result" in st.session_state:
        res = st.session_state.extract_result
        st.caption(f"Source: {'Google Gemini' if st.session_state.extract_mode == 'ai' else 'rule-based fallback'}")
        if res.get("error"):
            st.error(res["error"])
        acts = pd.DataFrame(res["actions"])
        if not acts.empty:
            for col in ("task", "owner", "source_quote"):
                if col in acts:
                    acts[col] = acts[col].map(lambda v: pv.unmask_text(v, name_map) if isinstance(v, str) else v)
            acts["verified"] = acts.get("verified", False).map({True: "✅ quote found", False: "⚠️ check manually"})
            st.dataframe(acts, hide_index=True, width="stretch")
            st.download_button("Download action items (CSV)", acts.to_csv(index=False),
                               file_name="action_items.csv")
        else:
            st.info("No action items found.")
        if res.get("decisions"):
            st.markdown("**Decisions**")
            for d in res["decisions"]:
                st.write("- " + pv.unmask_text(str(d), name_map))
        if res.get("risks"):
            st.markdown("**Risks**")
            for r in res["risks"]:
                st.write("- " + pv.unmask_text(str(r), name_map))

    st.divider()
    st.markdown("**📅 Meeting coordination: create a follow-up invite (.ics)**")
    m1, m2, m3 = st.columns(3)
    title = m1.text_input("Title", "Initiative follow-up sync")
    day = m2.date_input("Date", value=as_of + dt.timedelta(days=7), key="mdate")
    start = m3.time_input("Start (IST)", value=dt.time(11, 0))
    dur = st.slider("Duration (minutes)", 15, 90, 30, 15)
    s = dt.datetime.combine(day, start)
    e = s + dt.timedelta(minutes=dur)
    f = "%Y%m%dT%H%M%S"
    ics = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//ai-tracker//EN\r\nBEGIN:VEVENT\r\n"
           f"UID:{s.strftime(f)}@ai-tracker\r\nDTSTAMP:{dt.datetime.now(dt.timezone.utc).strftime(f)}Z\r\n"
           f"DTSTART;TZID=Asia/Kolkata:{s.strftime(f)}\r\nDTEND;TZID=Asia/Kolkata:{e.strftime(f)}\r\n"
           f"SUMMARY:{title}\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
    st.download_button("Download invite (.ics)", ics, file_name="follow_up.ics", mime="text/calendar")

# ---------------- Change comms ----------------
with tab_comms:
    st.subheader("Draft a change communication")
    change = st.text_area("What is changing?", "From 15 Nov, all project status updates move from email to the new shared tracker.")
    aud = st.selectbox("Who is the audience?", ["All project team members", "Regional leads", "Senior leadership"])
    if st.button("Draft message", key="comms"):
        txt, mode = ai.generate_change_comms(change, aud)
        st.session_state.comms_draft = txt
        st.session_state.comms_mode = mode
    if "comms_draft" in st.session_state:
        st.caption(f"Source: {'Google Gemini' if st.session_state.comms_mode == 'ai' else 'template fallback'} · "
                   "Placeholders in [brackets] must be filled by you.")
        st.text_area("Editable draft", st.session_state.comms_draft, height=240, key="comms_edit")

# ---------------- AI review log ----------------
with tab_log:
    st.subheader("AI-human collaboration log")
    st.write("Record every time you checked AI output. This becomes your interview story.")
    with st.form("log_form", clear_on_submit=True):
        out_type = st.selectbox("Output reviewed", ["Weekly status", "Action items", "Change comms"])
        wrong = st.text_input("What was wrong or missing?")
        fix = st.text_input("How did you check / fix it?")
        if st.form_submit_button("Add entry") and (wrong or fix):
            st.session_state.review_log.append(
                {"date": str(dt.date.today()), "output": out_type, "issue": wrong, "fix": fix})
    if st.session_state.review_log:
        log_df = pd.DataFrame(st.session_state.review_log)
        st.dataframe(log_df, hide_index=True, width="stretch")
        st.download_button("Download log (CSV)", log_df.to_csv(index=False), file_name="ai_review_log.csv")
