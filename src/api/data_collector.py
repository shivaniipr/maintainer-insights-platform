
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
    "user",
]


def fetch_items(
    owner,
    repo,
    item_type,
    limit=100,
    exclude_pull_requests=False,
):
    """Fetch issues or pull requests using the GitHub Search API."""
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

        # GitHub's search endpoint can return pull requests
        # alongside issues in some search situations.
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
    """Convert GitHub API records into a consistent data structure."""
    cleaned = []

    for item in items:
        user_data = item.get("user")

        cleaned.append(
            {
                "number": item.get("number"),
                "title": item.get("title"),
                "state": item.get("state"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "closed_at": item.get("closed_at"),
                "user": (
                    user_data.get("login")
                    if user_data
                    else None
                ),
            }
        )

    return cleaned


def collect_repository_data(owner, repo):
    """Fetch and return issue and pull request DataFrames."""
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
    """Save issue and pull request DataFrames as CSV files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    issues_path = DATA_DIR / "issues.csv"
    prs_path = DATA_DIR / "pull_requests.csv"

    issues_df.to_csv(issues_path, index=False)
    prs_df.to_csv(prs_path, index=False)


if __name__ == "__main__":
    try:
        issues_df, prs_df = collect_repository_data(
            "pandas-dev",
            "pandas",
        )

        save_repository_data(issues_df, prs_df)

        print("Issues collected:", len(issues_df))
        print("Pull requests collected:", len(prs_df))
        print("CSV files saved successfully.")

    except requests.exceptions.RequestException as error:
        print("GitHub API request failed:", error)

    except (OSError, ValueError) as error:
        print("Data collection or saving failed:", error)