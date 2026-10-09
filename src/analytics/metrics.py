
import pandas as pd


def calculate_issue_metrics(issues_df):
    """Calculate issue counts and identify old open issues."""
    if issues_df.empty:
        return {
            "total_issues": 0,
            "open_issues": 0,
            "closed_issues": 0,
            "aging_issues": 0,
        }

    issues = issues_df.copy()
    issues["created_at"] = pd.to_datetime(
    issues["created_at"], utc=True, format="mixed"
)

    open_issues = issues[issues["state"] == "open"]
    closed_issues = issues[issues["state"] == "closed"]

    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=30)
    aging_issues = open_issues[open_issues["created_at"] < cutoff]

    return {
        "total_issues": len(issues),
        "open_issues": len(open_issues),
        "closed_issues": len(closed_issues),
        "aging_issues": len(aging_issues),
    }


def calculate_pr_metrics(prs_df):
    """Calculate pull request counts and average open PR age."""
    if prs_df.empty:
        return {
            "total_pull_requests": 0,
            "open_pull_requests": 0,
            "closed_pull_requests": 0,
            "average_open_pr_age_days": 0,
        }

    prs = prs_df.copy()
    prs["created_at"] = pd.to_datetime(
    prs["created_at"], utc=True, format="mixed"
)

    open_prs = prs[prs["state"] == "open"]
    closed_prs = prs[prs["state"] == "closed"]

    now = pd.Timestamp.now(tz="UTC")
    ages = (now - open_prs["created_at"]).dt.total_seconds() / 86400

    return {
        "total_pull_requests": len(prs),
        "open_pull_requests": len(open_prs),
        "closed_pull_requests": len(closed_prs),
        "average_open_pr_age_days": (
            round(ages.mean(), 1) if not ages.empty else 0
        ),
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