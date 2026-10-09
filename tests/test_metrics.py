
import pandas as pd

from src.analytics.metrics import (
    calculate_issue_metrics,
    calculate_pr_metrics,
)


def test_issue_metrics():
    issues = pd.DataFrame([
        {
            "state": "open",
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "state": "open",
            "created_at": pd.Timestamp.now(tz="UTC").isoformat(),
        },
        {
            "state": "closed",
            "created_at": "2026-01-01T00:00:00Z",
        },
    ])

    result = calculate_issue_metrics(issues)

    assert result["total_issues"] == 3
    assert result["open_issues"] == 2
    assert result["closed_issues"] == 1
    assert result["aging_issues"] == 1


def test_pull_request_metrics():
    prs = pd.DataFrame([
        {
            "state": "open",
            "created_at": (
                pd.Timestamp.now(tz="UTC") -
                pd.Timedelta(days=10)
            ).isoformat(),
        },
        {
            "state": "closed",
            "created_at": "2026-01-01T00:00:00Z",
        },
    ])

    result = calculate_pr_metrics(prs)

    assert result["total_pull_requests"] == 2
    assert result["open_pull_requests"] == 1
    assert result["closed_pull_requests"] == 1
    assert result["average_open_pr_age_days"] >= 9


def test_empty_data():
    empty_df = pd.DataFrame(columns=["state", "created_at"])

    issue_result = calculate_issue_metrics(empty_df)
    pr_result = calculate_pr_metrics(empty_df)

    assert issue_result["total_issues"] == 0
    assert issue_result["aging_issues"] == 0
    assert pr_result["total_pull_requests"] == 0
    assert pr_result["average_open_pr_age_days"] == 0