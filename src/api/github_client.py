
import requests


GITHUB_API_URL = "https://api.github.com"


def get_repository(owner, repo):
    """Fetch basic information about a public GitHub repository."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    repository = get_repository("pandas-dev", "pandas")

    print("Repository:", repository["full_name"])
    print("Description:", repository["description"])
    print("Stars:", repository["stargazers_count"])
    print("Open issues:", repository["open_issues_count"])