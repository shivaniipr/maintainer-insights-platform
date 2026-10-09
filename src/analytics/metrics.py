
import pandas as pd


AGING_THRESHOLD_DAYS = 30


def _prepare_dates(df):
    """Convert date columns to UTC timestamps safely."""
    data = df.copy()

    for column in ["created_at", "closed_at", "merged_at"]:
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

    if "state" in data.columns:
        data["state"] = (
            data["state"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )
    else:
        data["state"] = ""

    return data


def _days_between(end_dates, start_dates):
    """Return non-negative durations in days, excluding invalid dates."""
    durations = (
        end_dates - start_dates
    ).dt.total_seconds() / 86400

    return durations[durations >= 0].dropna()


def _average(values):
    """Return a rounded average, or zero when no valid values exist."""
    return round(float(values.mean()), 1) if not values.empty else 0


def _median(values):
    """Return a rounded median, or zero when no valid values exist."""
    return round(float(values.median()), 1) if not values.empty else 0


def _percentage(part, whole):
    """Calculate a percentage safely."""
    return round(part / whole * 100, 1) if whole else 0


def calculate_issue_metrics(issues_df):
    """Calculate issue counts, aging, resolution times, and workload health."""
    if issues_df.empty:
        return {
            "total_issues": 0,
            "open_issues": 0,
            "closed_issues": 0,
            "aging_issues": 0,
            "aging_issue_percentage": 0,
            "issue_closure_rate": 0,
            "average_resolution_time_days": 0,
            "median_resolution_time_days": 0,
            "average_open_issue_age_days": 0,
            "median_open_issue_age_days": 0,
        }

    issues = _prepare_dates(issues_df)

    open_issues = issues[issues["state"] == "open"]
    closed_issues = issues[issues["state"] == "closed"]

    now = pd.Timestamp.now(tz="UTC")
    cutoff = now - pd.Timedelta(days=AGING_THRESHOLD_DAYS)

    aging_issues = open_issues[
        open_issues["created_at"] < cutoff
    ]

    open_ages = _days_between(
        pd.Series(now, index=open_issues.index),
        open_issues["created_at"],
    )

    resolution_times = _days_between(
        closed_issues["closed_at"],
        closed_issues["created_at"],
    )

    total = len(issues)
    open_count = len(open_issues)
    closed_count = len(closed_issues)

    return {
        "total_issues": total,
        "open_issues": open_count,
        "closed_issues": closed_count,
        "aging_issues": len(aging_issues),
        "aging_issue_percentage": _percentage(
            len(aging_issues), open_count
        ),
        "issue_closure_rate": _percentage(closed_count, total),
        "average_resolution_time_days": _average(resolution_times),
        "median_resolution_time_days": _median(resolution_times),
        "average_open_issue_age_days": _average(open_ages),
        "median_open_issue_age_days": _median(open_ages),
    }


def calculate_pr_metrics(prs_df):
    """Calculate PR counts, aging, closure, and merge-related metrics."""
    if prs_df.empty:
        return {
            "total_pull_requests": 0,
            "open_pull_requests": 0,
            "closed_pull_requests": 0,
            "average_open_pr_age_days": 0,
            "median_open_pr_age_days": 0,
            "aging_open_pull_requests": 0,
            "aging_open_pr_percentage": 0,
            "pr_closure_rate": 0,
            "average_pr_closing_time_days": 0,
            "median_pr_closing_time_days": 0,
            "merged_pull_requests": 0,
            "pr_merge_rate": 0,
            "merge_rate_available": False,
        }

    has_merge_data = "merged_at" in prs_df.columns

    prs = _prepare_dates(prs_df)

    open_prs = prs[prs["state"] == "open"]
    closed_prs = prs[prs["state"] == "closed"]

    now = pd.Timestamp.now(tz="UTC")
    cutoff = now - pd.Timedelta(days=AGING_THRESHOLD_DAYS)

    open_ages = _days_between(
        pd.Series(now, index=open_prs.index),
        open_prs["created_at"],
    )

    aging_open_prs = open_prs[
        open_prs["created_at"] < cutoff
    ]

    closing_times = _days_between(
        closed_prs["closed_at"],
        closed_prs["created_at"],
    )

    total = len(prs)
    open_count = len(open_prs)
    closed_count = len(closed_prs)

    if has_merge_data:
        merged_prs = prs[prs["merged_at"].notna()]
        merged_count = len(merged_prs)
        merge_rate = _percentage(merged_count, total)
    else:
        # Without merged_at, closed PRs cannot reliably be
        # distinguished from merged PRs.
        merged_count = 0
        merge_rate = 0

    return {
        "total_pull_requests": total,
        "open_pull_requests": open_count,
        "closed_pull_requests": closed_count,
        "average_open_pr_age_days": _average(open_ages),
        "median_open_pr_age_days": _median(open_ages),
        "aging_open_pull_requests": len(aging_open_prs),
        "aging_open_pr_percentage": _percentage(
            len(aging_open_prs), open_count
        ),
        "pr_closure_rate": _percentage(closed_count, total),
        "average_pr_closing_time_days": _average(closing_times),
        "median_pr_closing_time_days": _median(closing_times),
        "merged_pull_requests": merged_count,
        "pr_merge_rate": merge_rate,
        "merge_rate_available": has_merge_data,
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