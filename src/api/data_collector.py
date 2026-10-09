
import requests
import pandas as pd
from pathlib import Path

GITHUB_API_URL = "https://api.github.com"
DATA_DIR = Path("data")


def fetch_items(owner, repo, item_type, limit=100):
    """Fetch up to 100 issues or pull requests from GitHub."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/{item_type}"

    response = requests.get(
        url,
        params={
            "state": "all",
            "per_page": min(limit, 100),
            "sort": "created",
            "direction": "desc",
        },
        headers={"Accept": "application/vnd.github+json"},
        timeout=20,
    )
    response.raise_for_status()

    return response.json()[:limit]


def collect_repository_data(owner, repo):
    """Collect and structure issue and pull request data."""
    issues = fetch_items(owner, repo, "issues")
    pull_requests = fetch_items(owner, repo, "pulls")

    # GitHub's issues endpoint also includes pull requests.
    issues = [
        item for item in issues
        if "pull_request" not in item
    ]

    def clean_items(items):
        return [
            {
                "number": item["number"],
                "title": item["title"],
                "state": item["state"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
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