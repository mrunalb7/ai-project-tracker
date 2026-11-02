
"""AI layer powered by Google Gemini.

Privacy rules:
1. Only masked text should be sent to Gemini.
2. Never invent names, dates, numbers or causes.
3. All AI output is a draft for human review.
4. Rule-based fallbacks work when Gemini is unavailable.
"""
import json
import os

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
STATUS_SYSTEM = (
    "You are an operations analyst at a professional services firm. "
    "Write concise, client-ready weekly status reports. Use ONLY the facts "
    "provided. Never invent names, dates, numbers or causes. If something "
    "is unknown, say 'not stated'. Keep placeholders like Person A unchanged."
)

NOTES_SYSTEM = (
    "Extract action items from meeting notes. Return ONLY valid JSON with "
    "keys actions, decisions and risks. Each action must have task, owner, "
    "due_date and source_quote. Use null if owner or due date is not stated. "
    "source_quote must be copied exactly from the notes. Never guess."
)


def _client():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None

    from google import genai
    return genai.Client(api_key=key)


def ai_available():
    return bool(os.getenv("GEMINI_API_KEY"))


def _ask(system, user, max_tokens=900):
    client = _client()
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not set")

    response = client.models.generate_content(
        model=MODEL,
        contents=user,
        config={
            "system_instruction": system,
            "max_output_tokens": max_tokens,
            "temperature": 0.2,
        },
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response")

    return response.text


# ---------- Weekly status report ----------
def fallback_status(nums, at_risk_rows):
    lines = [
        "**Weekly Status (auto-generated, no AI)**",
        f"- Overall: {nums['completed']}/{nums['total']} tasks complete ({nums['completion_pct']}%).",
        f"- Attention needed: {nums['overdue']} overdue, {nums['blocked']} blocked, {nums['due_soon']} due within 3 days.",
        "",
        "**Items at risk**",
    ]
    for r in at_risk_rows:
        lines.append(
            f"- [{r['Risk']}] {r['Task']} ({r['Owner']}, due {r['Due Date']})"
        )
    return "\n".join(lines)


def generate_status_report(
    nums, at_risk_rows, audience="Project leadership", tone="Professional"
):
    prompt = (
        f"Audience: {audience}. Tone: {tone}.\n"
        "Write a weekly status report (max 180 words) with sections: "
        "Summary, Risks & Blockers, Next Steps. Suggest at most 3 next steps "
        "based only on the data.\n\n"
        f"KEY NUMBERS:\n{json.dumps(nums)}\n\n"
        f"AT-RISK ITEMS:\n{json.dumps(at_risk_rows, default=str)}"
    )

    if not ai_available():
        return fallback_status(nums, at_risk_rows), "fallback"

    try:
        return _ask(STATUS_SYSTEM, prompt), "ai"
    except Exception as exc:
        print(f"Gemini status report error: {exc}")
        return fallback_status(nums, at_risk_rows), "fallback"


# ---------- Change communication ----------
def generate_change_comms(change_description, audience, nums=None):
    prompt = (
        f"Draft a short change-communication email (max 150 words) "
        f"for: {audience}.\nChange: {change_description}\n"
        "Include what is changing, why it matters, what they need to do, "
        "and where to get help. Do not invent dates or links; use placeholders."
    )

    fallback = (
        "Subject: Upcoming change\n\nHi team,\n\n"
        + change_description
        + "\n\nPlease [action needed] by [date]. "
        "Questions? Contact [support].\n\nThanks"
    )

    if not ai_available():
        return fallback, "fallback"

    try:
        return _ask(STATUS_SYSTEM, prompt, 500), "ai"
    except Exception as exc:
        print(f"Gemini change communication error: {exc}")
        return fallback, "fallback"


# ---------- Meeting notes -> action items ----------
def fallback_extract(notes):
    """Simple rule-based extractor for offline use."""
    items = []
    keys = (
        "will ", "to send", "to follow", "needs to",
        "agreed to", "to report", "to begin"
    )

    for line in notes.splitlines():
        low = line.lower()
        if line.strip().startswith("-") and any(k in low for k in keys):
            quote = line.strip("- ").strip()
            items.append({
                "task": quote,
                "owner": None,
                "due_date": None,
                "source_quote": quote[:60],
            })

    return {"actions": items, "decisions": [], "risks": []}, "fallback"


def extract_actions(masked_notes):
    if not ai_available():
        return fallback_extract(masked_notes)

    try:
        raw = _ask(NOTES_SYSTEM, masked_notes, 1200).strip()
        raw = raw.removeprefix("```json").removeprefix("```")
        raw = raw.removesuffix("```").strip()

        data = json.loads(raw)

        if isinstance(data, list):
            actions = [item for item in data if isinstance(item, dict) and "task" in item]
            extras = next(
                (item for item in data if isinstance(item, dict)
                 and ("decisions" in item or "risks" in item)),
                {},
            )
        else:
            actions = data.get("actions", [])
            extras = data

        return {
            "actions": actions,
            "decisions": extras.get("decisions", []),
            "risks": extras.get("risks", []),
        }, "ai"

    except Exception as exc:
        print(f"Gemini meeting extraction error: {exc}")
        return fallback_extract(masked_notes)


def verify_quotes(actions, original_notes):
    """Check whether each source quote exists in the original notes."""
    low = original_notes.lower()

    for action in actions:
        quote = (action.get("source_quote") or "").lower().strip()
        action["verified"] = bool(quote) and quote in low

    return actions
