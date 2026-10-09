
from src.analytics.metrics import (
    calculate_issue_metrics,
    calculate_pr_metrics,
)


def compare_repository_data(
    repository_name,
    issues_df,
    prs_df,
):
    """Summarize collected issue and PR data for one repository."""

    issue_metrics = calculate_issue_metrics(issues_df)
    pr_metrics = calculate_pr_metrics(prs_df)

    return {
        "repository": repository_name,
        "issues_collected": len(issues_df),
        "pull_requests_collected": len(prs_df),
        "total_issues": issue_metrics["total_issues"],
        "open_issues": issue_metrics["open_issues"],
        "aging_issues": issue_metrics["aging_issues"],
        "issue_closure_rate": issue_metrics["issue_closure_rate"],
        "median_resolution_days": (
            issue_metrics["median_resolution_time_days"]
        ),
        "total_pull_requests": (
            pr_metrics["total_pull_requests"]
        ),
        "open_pull_requests": (
            pr_metrics["open_pull_requests"]
        ),
        "aging_open_pull_requests": (
            pr_metrics["aging_open_pull_requests"]
        ),
        "pr_closure_rate": pr_metrics["pr_closure_rate"],
        "median_pr_closing_days": (
            pr_metrics["median_pr_closing_time_days"]
        ),
        "merged_pull_requests": (
            pr_metrics["merged_pull_requests"]
        ),
        "pr_merge_rate": pr_metrics["pr_merge_rate"],
        "merge_rate_available": (
            pr_metrics["merge_rate_available"]
        ),
    }