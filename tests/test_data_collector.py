
import pytest
from unittest.mock import Mock, patch

from src.api.data_collector import fetch_items


@patch("src.api.data_collector.requests.get")
def test_fetch_issues_success(mock_get):
    """Test that issues are fetched successfully."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "items": [
            {"number": 1, "title": "First issue"},
            {"number": 2, "title": "Second issue"},
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_items("owner", "repo", "issues", limit=2)

    assert len(result) == 2
    assert result[0]["number"] == 1
    assert result[1]["title"] == "Second issue"

    params = mock_get.call_args.kwargs["params"]
    assert params["q"] == "repo:owner/repo is:issue"


@patch("src.api.data_collector.requests.get")
def test_fetch_pull_requests_success(mock_get):
    """Test that pull requests are fetched successfully."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "items": [
            {"number": 10, "title": "Fix a bug"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_items("owner", "repo", "pulls", limit=1)

    assert len(result) == 1
    assert result[0]["title"] == "Fix a bug"

    params = mock_get.call_args.kwargs["params"]
    assert params["q"] == "repo:owner/repo is:pr"


@patch("src.api.data_collector.requests.get")
def test_fetch_items_returns_empty_list(mock_get):
    """Test behavior when GitHub returns no results."""
    mock_response = Mock()
    mock_response.json.return_value = {"items": []}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_items("owner", "repo", "issues", limit=100)

    assert result == []
    mock_get.assert_called_once()


@patch("src.api.data_collector.requests.get")
def test_fetch_items_respects_limit(mock_get):
    """Test that the function returns no more than the requested limit."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "items": [
            {"number": 1},
            {"number": 2},
            {"number": 3},
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_items("owner", "repo", "issues", limit=2)

    assert len(result) == 2


@patch("src.api.data_collector.requests.get")
def test_fetch_items_handles_api_error(mock_get):
    """Test that GitHub API errors are raised to the caller."""
    import requests

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        "GitHub API request failed"
    )
    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        fetch_items("owner", "repo", "issues", limit=10)


def test_fetch_items_rejects_invalid_type():
    """Test that unsupported item types are rejected."""
    with pytest.raises(ValueError):
        fetch_items("owner", "repo", "invalid", limit=10)


def test_fetch_items_returns_empty_for_zero_limit():
    """Test behavior when the requested limit is zero."""
    result = fetch_items("owner", "repo", "issues", limit=0)

    assert result == []


def test_fetch_items_returns_empty_for_negative_limit():
    """Test behavior when the requested limit is negative."""
    result = fetch_items("owner", "repo", "issues", limit=-5)

    assert result == []