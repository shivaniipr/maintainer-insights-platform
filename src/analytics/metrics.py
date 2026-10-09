
import pandas as pd



def _prepare_dates(df):
    """Convert date columns to UTC timestamps safely."""
    data = df.copy()

    for column in ["created_at", "closed_at"]:
        if column in data.columns:
            data[column] = pd.to_datetime(
                data[column],
                utc=True,
                format="mixed",
                errors="coerce",
            )
        else:
            data[column] = pd.Series(
                pd.NaT,
                index=data.index,
                dtype="datetime64[ns, UTC]",
            )

    return data


def calculate_issue_metrics(issues_df):
    """Calculate issue counts, aging, and resolution time."""
    if issues_df.empty:
        return {
            "total_issues": 0,
            "open_issues": 0,
            "closed_issues": 0,
            "aging_issues": 0,
            "issue_closure_rate": 0,
            "average_resolution_time_days": 0,
        }

    issues = _prepare_dates(issues_df)

    open_issues = issues[issues["state"] == "open"]
    closed_issues = issues[issues["state"] == "closed"]

    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=30)

    aging_issues = open_issues[
        open_issues["created_at"] < cutoff
    ]

    resolution_times = (
        closed_issues["closed_at"] - closed_issues["created_at"]
    ).dt.total_seconds() / 86400

    resolution_times = resolution_times[
        resolution_times >= 0
    ].dropna()

    total = len(issues)
    closed_count = len(closed_issues)

    return {
        "total_issues": total,
        "open_issues": len(open_issues),
        "closed_issues": closed_count,
        "aging_issues": len(aging_issues),
        "issue_closure_rate": round(
            closed_count / total * 100, 1
        ),
        "average_resolution_time_days": round(
            resolution_times.mean(), 1
        ) if not resolution_times.empty else 0,
    }


def calculate_pr_metrics(prs_df):
    """Calculate PR counts, age, closure rate, and closing time."""
    if prs_df.empty:
        return {
            "total_pull_requests": 0,
            "open_pull_requests": 0,
            "closed_pull_requests": 0,
            "average_open_pr_age_days": 0,
            "pr_closure_rate": 0,
            "average_pr_closing_time_days": 0,
        }

    prs = _prepare_dates(prs_df)

    open_prs = prs[prs["state"] == "open"]
    closed_prs = prs[prs["state"] == "closed"]

    now = pd.Timestamp.now(tz="UTC")

    open_ages = (
        now - open_prs["created_at"]
    ).dt.total_seconds() / 86400

    open_ages = open_ages[open_ages >= 0].dropna()

    closing_times = (
        closed_prs["closed_at"] - closed_prs["created_at"]
    ).dt.total_seconds() / 86400

    closing_times = closing_times[
        closing_times >= 0
    ].dropna()

    total = len(prs)
    closed_count = len(closed_prs)

    return {
        "total_pull_requests": total,
        "open_pull_requests": len(open_prs),
        "closed_pull_requests": closed_count,
        "average_open_pr_age_days": round(
            open_ages.mean(), 1
        ) if not open_ages.empty else 0,
        "pr_closure_rate": round(
            closed_count / total * 100, 1
        ),
        "average_pr_closing_time_days": round(
            closing_times.mean(), 1
        ) if not closing_times.empty else 0,
    }


if __name__ == "__main__":
    issues_df = pd.read_csv("data/issues.csv")
    prs_df = pd.read_csv("data/pull_requests.csv")

    print("\nISSUE METRICS")
    for metric, value in calculate_issue_metrics(issues_df).items():
        print(f"{metric}: {value}")

    print("\nPULL REQUEST METRICS")
    for metric, value in calculate_pr_metrics(prs_df).items():
        print(f"{metric}: {value}")