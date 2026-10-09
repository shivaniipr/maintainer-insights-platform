import requests
import pandas as pd
from pathlib import Path

GITHUB_API_URL = "https://api.github.com"
DATA_DIR = Path("data")
PER_PAGE = 100


def fetch_items(owner, repo, item_type, limit=100,
                exclude_pull_requests=False):
    """Fetch issues or pull requests using GitHub Search API."""
    if limit <= 0:
        return []

    if item_type not in {"issues", "pulls"}:
        raise ValueError("item_type must be 'issues' or 'pulls'")

    # Search for issues and PRs separately to avoid mixed results.
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
            headers={"Accept": "application/vnd.github+json"},
            timeout=20,
        )
        response.raise_for_status()

        batch = response.json().get("items", [])

        if not batch:
            break

        items.extend(batch)

        if len(batch) < page_size:
            break

        page += 1

    return items[:limit]


def collect_repository_data(owner, repo):
    """Collect and structure issue and pull request data."""
    issues = fetch_items(
        owner, repo, "issues",
        limit=100,
        exclude_pull_requests=True,
    )

    pull_requests = fetch_items(
        owner, repo, "pulls",
        limit=100,
    )

    
def clean_items(items):
    return [
        {
            "number": item["number"],
            "title": item["title"],
            "state": item["state"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
            "closed_at": item.get("closed_at"),
            "user": (
                item["user"]["login"]
                if item.get("user")
                else None
            ),
        }
        for item in items
    ]

    return (
        pd.DataFrame(clean_items(issues)),
        pd.DataFrame(clean_items(pull_requests)),
    )


def save_repository_data(issues_df, prs_df):
    """Save the collected records to CSV files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    issues_df.to_csv(DATA_DIR / "issues.csv", index=False)
    prs_df.to_csv(DATA_DIR / "pull_requests.csv", index=False)


if __name__ == "__main__":
    issues_df, prs_df = collect_repository_data(
        "pandas-dev", "pandas"
    )
    save_repository_data(issues_df, prs_df)

    print("Issues collected:", len(issues_df))
    print("Pull requests collected:", len(prs_df))
    print("Data saved successfully.")