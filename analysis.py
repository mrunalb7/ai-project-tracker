"""Data analysis: clean the tracker, compute status, flag risks."""
import pandas as pd

REQUIRED_COLUMNS = ["Task ID", "Initiative", "Task", "Owner", "Status", "Priority", "Due Date"]
VALID_STATUS = ["Not Started", "In Progress", "Blocked", "Completed"]


def load_tracker(file):
    """Read CSV or Excel into a DataFrame."""
    name = getattr(file, "name", str(file)).lower()
    df = pd.read_excel(file) if name.endswith((".xlsx", ".xls")) else pd.read_csv(file)
    return df


def validate(df):
    """Return a list of human-readable data-quality issues (empty list = clean)."""
    issues = []
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        issues.append(f"Missing required columns: {', '.join(missing)}")
        return issues
    bad_status = df[~df["Status"].isin(VALID_STATUS)]
    if len(bad_status):
        issues.append(f"{len(bad_status)} row(s) have an unrecognised Status.")
    if df["Owner"].isna().any():
        issues.append(f"{int(df['Owner'].isna().sum())} task(s) have no Owner.")
    if df["Task ID"].duplicated().any():
        issues.append("Duplicate Task IDs found.")
    if pd.to_datetime(df["Due Date"], errors="coerce", format="mixed").isna().any():
        issues.append("Some Due Dates are missing or not valid dates.")
    return issues


def enrich(df, today=None):
    """Add computed columns: days overdue, days to due, risk flag."""
    today = pd.Timestamp(today or pd.Timestamp.today().normalize())
    df = df.copy()
    df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
    if "Last Update" in df.columns:
        df["Last Update"] = pd.to_datetime(df["Last Update"], errors="coerce")
        df["Days Since Update"] = (today - df["Last Update"]).dt.days
    else:
        df["Days Since Update"] = 0
    df["Days To Due"] = (df["Due Date"] - today).dt.days

    def flag(row):
        if row["Status"] == "Completed":
            return "Done"
        if row["Status"] == "Blocked":
            return "Blocked"
        if row["Days To Due"] < 0:
            return "Overdue"
        if row["Days To Due"] <= 3:
            return "Due Soon"
        if row["Status"] == "Not Started" and row["Days Since Update"] > 7:
            return "Stale"
        return "On Track"

    df["Risk"] = df.apply(flag, axis=1)
    return df


def summary_numbers(df):
    """Key numbers for the dashboard and for the AI prompt."""
    total = len(df)
    done = int((df["Status"] == "Completed").sum())
    return {
        "total": total,
        "completed": done,
        "completion_pct": round(100 * done / total, 1) if total else 0,
        "overdue": int((df["Risk"] == "Overdue").sum()),
        "blocked": int((df["Risk"] == "Blocked").sum()),
        "due_soon": int((df["Risk"] == "Due Soon").sum()),
        "stale": int((df["Risk"] == "Stale").sum()),
    }


def by_initiative(df):
    """Progress per initiative."""
    g = df.groupby("Initiative").agg(
        Tasks=("Task ID", "count"),
        Completed=("Status", lambda s: int((s == "Completed").sum())),
        At_Risk=("Risk", lambda s: int(s.isin(["Overdue", "Blocked", "Due Soon"]).sum())),
    )
    g["Completion %"] = (100 * g["Completed"] / g["Tasks"]).round(0)
    return g.reset_index()


def workload(df):
    """Open tasks per owner (helps spot overloaded people)."""
    open_df = df[df["Status"] != "Completed"]
    return open_df.groupby("Owner")["Task ID"].count().sort_values(ascending=False).rename("Open tasks")
