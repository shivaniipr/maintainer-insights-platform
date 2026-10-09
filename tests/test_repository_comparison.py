
import pandas as pd

from src.analytics.metrics import (
    calculate_issue_metrics,
    calculate_pr_metrics,
)
from src.analytics.repository_comparison import compare_repository_data


def test_comparison_returns_repository_name_and_record_counts():
    issues = pd.DataFrame(
        [
            {
                "number": 1,
                "title": "Issue one",
                "state": "open",
                "created_at": "2025-01-01T00:00:00Z",
                "closed_at": None,
            },
            {
                "number": 2,
                "title": "Issue two",
                "state": "closed",
                "created_at": "2025-01-01T00:00:00Z",
                "closed_at": "2025-01-03T00:00:00Z",
            },
        ]
    )

    pull_requests = pd.DataFrame(
        [
            {
                "number": 1,
                "title": "PR one",
                "state": "open",
                "created_at": "2025-01-01T00:00:00Z",
                "closed_at": None,
                "merged_at": None,
            }
        ]
    )

    result = compare_repository_data(
        "example/project",
        issues,
        pull_requests,
    )

    assert result["repository"] == "example/project"
    assert result["issues_collected"] == 2
    assert result["pull_requests_collected"] == 1


def test_comparison_matches_existing_issue_metrics():
    issues = pd.DataFrame(
        [
            {
                "number": 1,
                "state": "open",
                "created_at": "2025-01-01T00:00:00Z",
                "closed_at": None,
            },
            {
                "number": 2,
                "state": "closed",
                "created_at": "2025-01-01T00:00:00Z",
                "closed_at": "2025-01-03T00:00:00Z",
            },
        ]
    )

    pull_requests = pd.DataFrame(
        columns=["state", "created_at", "closed_at", "merged_at"]
    )

    result = compare_repository_data(
        "example/project",
        issues,
        pull_requests,
    )
    expected = calculate_issue_metrics(issues)

    assert result["total_issues"] == expected["total_issues"]
    assert result["open_issues"] == expected["open_issues"]
    assert result["aging_issues"] == expected["aging_issues"]
    assert result["issue_closure_rate"] == expected["issue_closure_rate"]
    assert (
        result["median_resolution_days"]
        == expected["median_resolution_time_days"]
    )


def test_comparison_matches_existing_pull_request_metrics():
    issues = pd.DataFrame(
        columns=["state", "created_at", "closed_at"]
    )

    pull_requests = pd.DataFrame(
        [
            {
                "number": 1,
                "state": "closed",
                "created_at": "2025-01-01T00:00:00Z",
                "closed_at": "2025-01-03T00:00:00Z",
                "merged_at": "2025-01-02T00:00:00Z",
            },
            {
                "number": 2,
                "state": "open",
                "created_at": "2025-01-01T00:00:00Z",
                "closed_at": None,
                "merged_at": None,
            },
        ]
    )

    result = compare_repository_data(
        "example/project",
        issues,
        pull_requests,
    )
    expected = calculate_pr_metrics(pull_requests)

    assert (
        result["total_pull_requests"]
        == expected["total_pull_requests"]
    )
    assert (
        result["open_pull_requests"]
        == expected["open_pull_requests"]
    )
    assert (
        result["merged_pull_requests"]
        == expected["merged_pull_requests"]
    )
    assert result["pr_closure_rate"] == expected["pr_closure_rate"]
    assert (
        result["median_pr_closing_days"]
        == expected["median_pr_closing_time_days"]
    )
    assert result["merge_rate_available"] == expected["merge_rate_available"]


def test_comparison_handles_empty_dataframes():
    issues = pd.DataFrame(
        columns=["state", "created_at", "closed_at"]
    )
    pull_requests = pd.DataFrame(
        columns=["state", "created_at", "closed_at", "merged_at"]
    )

    result = compare_repository_data(
        "example/empty-project",
        issues,
        pull_requests,
    )

    assert result["repository"] == "example/empty-project"
    assert result["issues_collected"] == 0
    assert result["pull_requests_collected"] == 0
    assert result["total_issues"] == 0
    assert result["total_pull_requests"] == 0
    assert result["open_issues"] == 0
    assert result["open_pull_requests"] == 0