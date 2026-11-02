"""Small tests - run with: python test_core.py   (shows you test discipline)."""
import pandas as pd
import analysis as an
import privacy as pv
import ai_helpers as ai


def test_masking():
    nm = pv.build_name_map(["Anita Rao", "Rahul Mehta"])
    out = pv.mask_text("Anita Rao (anita.rao@example.com) call +91 98765 43210, Rahul to follow up", nm)
    assert "anita" not in out.lower() and "rahul" not in out.lower(), out
    assert "[EMAIL]" in out and "[PHONE]" in out, out
    assert pv.unmask_text(out, nm).count("Anita Rao") >= 1


def test_risk_flags():
    df = an.load_tracker("data/sample_tracker.csv")
    assert an.validate(df) == []
    e = an.enrich(df, today="2026-11-03")
    assert e.loc[e["Task ID"] == "T006", "Risk"].iloc[0] == "Blocked"
    assert e.loc[e["Task ID"] == "T002", "Risk"].iloc[0] == "Overdue"
    assert e.loc[e["Task ID"] == "T003", "Risk"].iloc[0] == "Done"
    n = an.summary_numbers(e)
    assert n["total"] == 12 and n["completed"] == 2


def test_validation_catches_problems():
    bad = pd.DataFrame({"Task ID": ["1", "1"], "Initiative": ["x", "x"], "Task": ["a", "b"],
                        "Owner": [None, "Z"], "Status": ["Done??", "Completed"],
                        "Priority": ["High", "Low"], "Due Date": ["not a date", "2026-11-01"]})
    assert len(an.validate(bad)) >= 3


def test_quote_verification():
    notes = "Rahul will send the reminder by Wednesday."
    acts = [{"task": "x", "source_quote": "will send the reminder"},
            {"task": "y", "source_quote": "invented sentence"}]
    out = ai.verify_quotes(acts, notes)
    assert out[0]["verified"] and not out[1]["verified"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
