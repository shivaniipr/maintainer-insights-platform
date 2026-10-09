
import requests
import pandas as pd
from pathlib import Path

GITHUB_API_URL = "https://api.github.com"
DATA_DIR = Path("data")
PER_PAGE = 100

DATA_COLUMNS = [
    "number",
    "title",
    "state",
    "created_at",
    "updated_at",
    "closed_at",
    "merged_at",
    "user",
]


def fetch_items(
    owner,
    repo,
    item_type,
    limit=100,
    exclude_pull_requests=False,
):
    """Fetch issues or pull requests using GitHub Search API."""
    if limit <= 0:
        return []

    if item_type not in {"issues", "pulls"}:
        raise ValueError("item_type must be 'issues' or 'pulls'")

    item_filter = "is:issue" if item_type == "issues" else "is:pr"
    url = f"{GITHUB_API_URL}/search/issues"

    items = []
    page = 1

    while len(items) < limit:
        page_size = min(PER_PAGE, limit - len(items))

        response = requests.get(
            url,
            params={
                "q": f"repo:{owner}/{repo} {item_filter}",
                "per_page": page_size,
                "page": page,
                "sort": "created",
                "order": "desc",
            },
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Maintainer-Insights-Platform",
            },
            timeout=20,
        )
        response.raise_for_status()

        batch = response.json().get("items", [])

        if not batch:
            break

        if item_type == "issues" and exclude_pull_requests:
            batch = [
                item for item in batch
                if "pull_request" not in item
            ]

        items.extend(batch)

        if len(items) >= limit:
            break

        page += 1

    return items[:limit]


def clean_items(items):
    """Convert GitHub API records into consistent dictionaries."""
    cleaned = []

    for item in items:
        user_data = item.get("user")
        pull_request_data = item.get("pull_request") or {}

        # Search API responses may expose merge information inside
        # the pull_request object rather than at the top level.
        merged_at = item.get("merged_at")

        if merged_at is None:
            merged_at = pull_request_data.get("merged_at")

        cleaned.append(
            {
                "number": item.get("number"),
                "title": item.get("title"),
                "state": item.get("state"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "closed_at": item.get("closed_at"),
                "merged_at": merged_at,
                "user": (
                    user_data.get("login")
                    if user_data
                    else None
                ),
            }
        )

    return cleaned


def collect_repository_data(owner, repo):
    """Fetch issues and pull requests as DataFrames."""
    issues = fetch_items(
        owner,
        repo,
        "issues",
        limit=100,
        exclude_pull_requests=True,
    )

    pull_requests = fetch_items(
        owner,
        repo,
        "pulls",
        limit=100,
    )

    issues_df = pd.DataFrame(
        clean_items(issues),
        columns=DATA_COLUMNS,
    )

    prs_df = pd.DataFrame(
        clean_items(pull_requests),
        columns=DATA_COLUMNS,
    )

    return issues_df, prs_df


def save_repository_data(issues_df, prs_df):
    """Save collected records to CSV files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    issues_df.to_csv(
        DATA_DIR / "issues.csv",
        index=False,
    )

    prs_df.to_csv(
        DATA_DIR / "pull_requests.csv",
        index=False,
    )


if __name__ == "__main__":
    try:
        issues_df, prs_df = collect_repository_data(
            "pandas-dev",
            "pandas",
        )

        save_repository_data(issues_df, prs_df)

        print("Issues collected:", len(issues_df))
        print("Pull requests collected:", len(prs_df))
        print("Issue columns:", list(issues_df.columns))
        print("PR columns:", list(prs_df.columns))
        print("CSV files saved successfully.")

        if "merged_at" in prs_df.columns:
            merged_count = prs_df["merged_at"].notna().sum()
            print("PRs with merge timestamps:", merged_count)

    except requests.exceptions.RequestException as error:
        print("GitHub API request failed:", error)

    except (OSError, ValueError) as error:
        print("Data collection or saving failed:", error)