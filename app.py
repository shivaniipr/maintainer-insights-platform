
from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from src.api.data_collector import collect_repository_data, save_repository_data
from src.database.db import save_to_database
from src.analytics.metrics import calculate_issue_metrics, calculate_pr_metrics


# ==================================================
# 1. CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ISSUES_FILE = DATA_DIR / "issues.csv"
PRS_FILE = DATA_DIR / "pull_requests.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Maintainer Insights Platform",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG_COLOR = "#0B1120"
SIDEBAR_COLOR = "#10192A"
CARD_COLOR = "#151F32"
GRID_COLOR = "#293951"
TEXT_COLOR = "#E5EDF8"
MUTED_COLOR = "#9AABC2"
BLUE = "#60A5FA"
GREEN = "#34D399"
AMBER = "#FBBF24"
RED = "#F87171"


# ==================================================
# 2. MONOCHROME SVG ICONS
# ==================================================

def svg_icon(name, size=24, color=BLUE):
    """Return a solid, single-colour SVG icon."""

    paths = {
        "brand": """
            <path d="M3 3h4v18H3zM9 11h4v10H9zM15 6h4v15h-4zM21 2h2v19h-2z"/>
        """,
        "github": """
            <path d="M12 .8a11.2 11.2 0 0 0-3.54 21.83c.56.1.77-.24.77-.54v-2.1c-3.14.68-3.8-1.33-3.8-1.33-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 .1.76 2.1 3.08 1.6.1-.72.4-1.22.7-1.5-2.5-.28-5.12-1.25-5.12-5.56 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.44.1-2.99 0 0 .95-.3 3.08 1.16a10.7 10.7 0 0 1 5.6 0c2.13-1.46 3.08-1.16 3.08-1.16.6 1.55.22 2.71.1 2.99.72.79 1.16 1.8 1.16 3.03 0 4.32-2.63 5.28-5.14 5.56.4.35.76 1.02.76 2.06v3.05c0 .3.2.65.78.54A11.2 11.2 0 0 0 12 .8Z"/>
        """,
        "fetch": """
            <path d="M12 3a9 9 0 0 1 8.49 6h-3.1a6 6 0 0 0-10.12-1.6L10 10H3V3l2.13 2.13A8.96 8.96 0 0 1 12 3Zm9 8v7l-2.13-2.13A8.98 8.98 0 0 1 12 21a9 9 0 0 1-8.49-6h3.1a6 6 0 0 0 10.12 1.6L14 14h7v-3Z"/>
        """,
        "about": """
            <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm1 15h-2v-6h2Zm0-8h-2V7h2Z"/>
        """,
        "overview": """
            <path d="M3 3h3v18H3zM8 12h4v9H8zM14 7h4v14h-4zM20 2h2v19h-2z"/>
        """,
        "issues": """
            <path d="M9 2h6a2 2 0 0 1 2 2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2-2Zm0 2v2h6V4H9Zm-2 6v2h10v-2H7Zm0 4v2h10v-2H7Zm0 4v2h7v-2H7Z"/>
        """,
        "pulls": """
            <path d="M6 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm0 2a1 1 0 1 1 0 2 1 1 0 0 1 0-2Zm0 10a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm0 2a1 1 0 1 1 0 2 1 1 0 0 1 0-2ZM18 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm0 2a1 1 0 1 1 0 2 1 1 0 0 1 0-2ZM5 8h2v6H5zm2-3h5a7 7 0 0 1 7 7v2h-2v-2a5 5 0 0 0-5-5H7z"/>
        """,
        "contributors": """
            <path d="M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8-1a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM9 13c-3.3 0-6 1.7-6 4v4h12v-4c0-2.3-2.7-4-6-4Zm8-1c-.8 0-1.5.1-2.2.3 1.4 1 2.2 2.3 2.2 3.7v4h4v-3c0-2.3-1.8-5-4-5Z"/>
        """,
    }

    path = paths[name]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="{color}" aria-hidden="true">{path}</svg>'
    )


# ==================================================
# 3. PROFESSIONAL THEME AND STYLES
# ==================================================

st.markdown(
    """
    <style>
    html, body, [class*="css"], [data-testid="stApp"],
    [data-testid="stMarkdownContainer"], input, textarea, button, select {
        font-family: "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    .stApp {
        background: #0B1120;
        color: #E5EDF8;
        font-size: 15px;
    }

    [data-testid="stHeader"] {
        background: rgba(11,17,32,.96);
    }

    [data-testid="stMainBlockContainer"] {
        padding: 1.5rem 2rem 2rem;
        max-width: 100%;
        overflow: visible;
    }

    [data-testid="stSidebar"] {
        background: #10192A;
        border-right: 1px solid #293951;
    }

    [data-testid="stSidebar"] * {
        color: #E5EDF8;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #151F32 !important;
        color: #E5EDF8 !important;
        border-color: #34445D !important;
        border-radius: 8px;
    }

    [data-testid="stSidebar"] h2 {
        font-size: 1.3rem;
        font-weight: 750;
    }

    [data-testid="stSidebar"] h3 {
        font-size: 1rem;
        font-weight: 650;
    }

    /* Sidebar branding */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
        box-sizing: border-box;
        padding: 15px 12px;
        margin: 2px 0 18px;
        border: 1px solid #344B6B;
        border-radius: 13px;
        background: #151F32;
        color: #F8FAFC;
        font-size: 16px;
        font-weight: 750;
        line-height: 1.4;
    }

    .sidebar-brand svg,
    .sidebar-item svg {
        flex-shrink: 0;
        display: block;
    }

    .sidebar-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 3px;
        color: #D3DFEF;
        font-size: 14px;
        font-weight: 650;
    }

    .sidebar-item svg {
        width: 22px;
        height: 22px;
    }

    /* Full, visible rounded heading tile */

.hero {
    width: 100%;
    box-sizing: border-box;
    padding: 32px 36px;
    margin: 12px 0 28px 0;
    background: transparent;
    border: none;
    border-radius: 0;
    overflow: visible;
    min-height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.hero h1 {
    margin: 0 0 12px 0;
    padding: 0;
    line-height: 1.3;
    color: #E5EDF8;
}

.hero p {
    margin: 0;
    padding: 0;
    line-height: 1.7;
    color: #9AABC2;
}

    .section-note {
        color: #9AABC2;
        font-size: 14px;
        line-height: 1.7;
    }

    h1, h2, h3, h4 {
        color: #F1F5F9;
        font-family: "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        letter-spacing: -.35px;
    }

    h2 { font-size: 1.5rem; font-weight: 700; }
    h3 { font-size: 1.2rem; font-weight: 650; }
    h4 { font-size: 1rem; font-weight: 650; }

    div[data-testid="stMetric"] {
        background: #151F32;
        border: 1px solid #293951;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 6px 18px rgba(0,0,0,.12);
    }

    div[data-testid="stMetricLabel"] {
        color: #9AABC2;
        font-size: .9rem;
    }

    div[data-testid="stMetricValue"] {
        color: #F1F5F9;
        font-size: 1.8rem;
        font-weight: 750;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #151F32;
        border-radius: 14px;
        border-color: #293951;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 9px;
        font-weight: 600;
        min-height: 42px;
        font-size: .9rem;
        transition: border-color .15s ease, background-color .15s ease;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        border-color: #60A5FA;
        color: #93C5FD;
    }

    /* Four equal-width navigation cards */
    .navigation-icon {
        min-height: 36px;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 6px;
    }

    .navigation-icon svg {
        width: 30px;
        height: 30px;
        display: block;
    }

    div.st-key-navigation_overview button,
    div.st-key-navigation_issues button,
    div.st-key-navigation_pull_requests button,
    div.st-key-navigation_contributors button {
        width: 100%;
        min-height: 48px;
        border-radius: 10px;
        font-weight: 650;
        border: 1px solid #293951;
        background: #151F32;
        color: #D3DFEF;
    }

    /* The active button is assigned a primary button type in Python */
    div.st-key-navigation_overview button[kind="primary"],
    div.st-key-navigation_issues button[kind="primary"],
    div.st-key-navigation_pull_requests button[kind="primary"],
    div.st-key-navigation_contributors button[kind="primary"] {
        background: #1D3555;
        color: #FFFFFF;
        border: 1px solid #60A5FA;
        box-shadow: inset 0 -2px 0 #60A5FA;
    }

    div.st-key-navigation_overview button:hover,
    div.st-key-navigation_issues button:hover,
    div.st-key-navigation_pull_requests button:hover,
    div.st-key-navigation_contributors button:hover {
        background: #1D3555;
        border-color: #60A5FA;
        color: #FFFFFF;
    }

    div[data-testid="stPlotlyChart"] {
        background: #151F32;
        border: 1px solid #293951;
        border-radius: 14px;
        padding: 8px;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #293951;
        border-radius: 10px;
        overflow: hidden;
    }

    hr { border-color: #293951; }

    [data-testid="stProgressBar"] > div > div {
        background-color: #60A5FA;
    }

    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1rem .8rem 1.5rem;
        }
        .hero {
            padding: 20px;
            border-radius: 14px;
        }
        .hero h1 { font-size: 24px; }
        .navigation-icon svg {
            width: 24px;
            height: 24px;
        }
        div.st-key-navigation_overview button,
        div.st-key-navigation_issues button,
        div.st-key-navigation_pull_requests button,
        div.st-key-navigation_contributors button {
            font-size: 12px;
            padding: 4px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# 4. HELPER FUNCTIONS
# ==================================================

@st.cache_data
def load_csv_data(file_path):
    """Load a CSV file safely and cache its contents."""
    if not file_path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(file_path)
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ):
        return pd.DataFrame()


def display_dataframe(dataframe, message):
    if dataframe.empty:
        st.info(message)
    else:
        st.dataframe(dataframe, use_container_width=True, hide_index=True)


def show_empty_state(title, description):
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.write(description)


def make_state_chart(dataframe, title):
    if dataframe.empty or "state" not in dataframe.columns:
        st.info(
            f"No {title.lower()} data is available yet. "
            "Fetch repository data from the sidebar."
        )
        return

    chart_data = (
        dataframe["state"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .str.title()
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Records")
    )

    figure = px.bar(
        chart_data,
        x="Status",
        y="Records",
        color="Status",
        text="Records",
        color_discrete_map={
            "Open": BLUE,
            "Closed": GREEN,
            "Unknown": "#94A3B8",
        },
        template="plotly_dark",
    )
    figure.update_traces(
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0,
    )
    figure.update_layout(
        title=title,
        height=350,
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor="#111A2B",
        font=dict(
            family="Inter, Segoe UI, Roboto, Arial, sans-serif",
            color=TEXT_COLOR,
            size=12,
        ),
        showlegend=False,
        margin=dict(t=65, b=45, l=35, r=25),
        xaxis=dict(title="Status", showgrid=False),
        yaxis=dict(
            title="Number of records",
            rangemode="tozero",
            gridcolor=GRID_COLOR,
        ),
    )
    st.plotly_chart(
        figure,
        use_container_width=True,
        config={"displayModeBar": False},
        theme=None,
    )


def make_turnaround_chart(issue_metrics, pr_metrics):
    chart_data = pd.DataFrame([
        {
            "Metric": "Issue resolution",
            "Duration": "Average",
            "Days": issue_metrics.get("average_resolution_time_days", 0),
        },
        {
            "Metric": "Issue resolution",
            "Duration": "Median",
            "Days": issue_metrics.get("median_resolution_time_days", 0),
        },
        {
            "Metric": "PR closing",
            "Duration": "Average",
            "Days": pr_metrics.get("average_pr_closing_time_days", 0),
        },
        {
            "Metric": "PR closing",
            "Duration": "Median",
            "Days": pr_metrics.get("median_pr_closing_time_days", 0),
        },
    ])

    figure = px.bar(
        chart_data,
        x="Metric",
        y="Days",
        color="Duration",
        barmode="group",
        text="Days",
        color_discrete_map={"Average": BLUE, "Median": GREEN},
        template="plotly_dark",
    )
    figure.update_traces(
        texttemplate="%{y:.1f}",
        textposition="outside",
        cliponaxis=False,
    )
    figure.update_layout(
        title="Average vs. median turnaround time",
        height=390,
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor="#111A2B",
        font=dict(
            family="Inter, Segoe UI, Roboto, Arial, sans-serif",
            color=TEXT_COLOR,
            size=12,
        ),
        yaxis=dict(
            title="Days",
            rangemode="tozero",
            gridcolor=GRID_COLOR,
        ),
        xaxis=dict(title=""),
        legend_title_text="Duration",
        margin=dict(t=65, b=45, l=35, r=25),
    )
    st.plotly_chart(
        figure,
        use_container_width=True,
        config={"displayModeBar": False},
        theme=None,
    )


def make_merge_chart(pr_metrics, chart_key):
    if not pr_metrics.get("merge_rate_available", False):
        st.info(
            "Merge analytics are unavailable because this dataset "
            "does not include merge timestamps."
        )
        return

    merged = pr_metrics.get("merged_pull_requests", 0)
    closed = pr_metrics.get("closed_pull_requests", 0)
    not_merged = max(closed - merged, 0)

    chart_data = pd.DataFrame({
        "Outcome": ["Merged", "Closed without merge"],
        "Pull requests": [merged, not_merged],
    })

    figure = px.bar(
        chart_data,
        x="Outcome",
        y="Pull requests",
        color="Outcome",
        text="Pull requests",
        color_discrete_map={
            "Merged": GREEN,
            "Closed without merge": AMBER,
        },
        template="plotly_dark",
    )
    figure.update_traces(
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0,
    )
    figure.update_layout(
        title="Pull request outcomes",
        height=350,
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor="#111A2B",
        font=dict(
            family="Inter, Segoe UI, Roboto, Arial, sans-serif",
            color=TEXT_COLOR,
            size=12,
        ),
        showlegend=False,
        xaxis=dict(title="", showgrid=False),
        yaxis=dict(
            title="Pull requests",
            rangemode="tozero",
            gridcolor=GRID_COLOR,
        ),
        margin=dict(t=65, b=45, l=35, r=25),
    )
    st.plotly_chart(
        figure,
        use_container_width=True,
        config={"displayModeBar": False},
        theme=None,
        key=chart_key,
    )


# ==================================================
# 5. SIDEBAR
# ==================================================

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand">
            {svg_icon("brand", 30)}
            <span>Maintainer Insights</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="sidebar-item">
            {svg_icon("github", 23)}
            <span>GitHub Repository</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    owner = st.text_input(
        "Repository owner",
        value="pandas-dev",
        help="Example: pandas-dev",
    )
    repo = st.text_input(
        "Repository name",
        value="pandas",
        help="Example: pandas",
    )

    fetch_clicked = st.button(
    "↻  Fetch Latest GitHub Data",
    key="fetch_latest_github_data",
    use_container_width=True,
    type="primary",
    )



    st.divider()

    st.markdown(
        f"""
        <div class="sidebar-item">
            {svg_icon("about", 22)}
            <span>About This Platform</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Analyze issue backlogs, pull requests, and contributor "
        "participation using GitHub repository data."
    )
    st.markdown("**Data source:** GitHub REST API")
    st.markdown("**Data storage:** CSV + SQLite")


# ==================================================
# 6. FETCH AND SAVE DATA
# ==================================================

if fetch_clicked:
    if not owner.strip() or not repo.strip():
        st.sidebar.error(
            "Please enter both the repository owner and repository name."
        )
    else:
        try:
            repository_owner = owner.strip()
            repository_name = repo.strip()

            with st.spinner(
                f"Fetching {repository_owner}/{repository_name}..."
            ):
                new_issues, new_prs = collect_repository_data(
                    repository_owner,
                    repository_name,
                )
                save_repository_data(new_issues, new_prs)
                save_to_database(
                    repository_owner,
                    repository_name,
                    new_issues,
                    new_prs,
                )

            st.session_state["last_fetched_repo"] = (
                f"{repository_owner}/{repository_name}"
            )
            st.session_state["fetch_success"] = (
                f"Successfully fetched {len(new_issues)} issues and "
                f"{len(new_prs)} pull requests from "
                f"{repository_owner}/{repository_name}. "
                "CSV files and SQLite database updated."
            )
            load_csv_data.clear()
            st.rerun()

        except Exception as error:
            st.sidebar.error(
                "Could not fetch or save repository data. Check the "
                "repository name, internet connection, and GitHub API."
            )
            st.sidebar.caption(f"Details: {error}")


# ==================================================
# 7. DASHBOARD HEADER
# ==================================================

st.markdown(
    """
    <div class="hero">
        <h1>Open-Source Maintainer Insights Platform</h1>
        <p>
            Understand repository health, monitor issue backlogs,
            analyze pull requests, and explore contributor activity.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("fetch_success"):
    st.success(st.session_state["fetch_success"])

selected_repo = st.session_state.get("last_fetched_repo")
if selected_repo:
    st.caption(f"Last refreshed repository: {selected_repo}")


# ==================================================
# 8. LOAD DATA AND METRICS
# ==================================================

issues_df = load_csv_data(ISSUES_FILE)
prs_df = load_csv_data(PRS_FILE)

issue_metrics = calculate_issue_metrics(issues_df)
pr_metrics = calculate_pr_metrics(prs_df)

if issues_df.empty and prs_df.empty:
    show_empty_state(
        "Welcome to Maintainer Insights",
        "No repository records have been loaded yet. Choose a public "
        "GitHub repository in the sidebar and click Fetch latest GitHub data.",
    )


# ==================================================
# 9. FOUR-SECTION NAVIGATION
# ==================================================

NAV_ITEMS = [
    ("Overview", "overview"),
    ("Issues", "issues"),
    ("Pull Requests", "pulls"),
    ("Contributors", "contributors"),
]

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Overview"


def render_navigation_item(label, icon_name):
    """Show an SVG above a button and highlight the selected section."""

    active = st.session_state["active_tab"] == label

    st.markdown(
        f'<div class="navigation-icon">{svg_icon(icon_name, 30)}</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        label,
        key=f"navigation_{label.lower().replace(' ', '_')}",
        use_container_width=True,
        type="primary" if active else "secondary",
    ):
        if st.session_state["active_tab"] != label:
            st.session_state["active_tab"] = label
            st.rerun()


nav_columns = st.columns(4, gap="small")
for column, (label, icon_name) in zip(nav_columns, NAV_ITEMS):
    with column:
        render_navigation_item(label, icon_name)

st.divider()


# ==================================================
# 10. OVERVIEW
# ==================================================

if st.session_state["active_tab"] == "Overview":
    st.subheader("Repository overview")
    st.markdown(
        '<p class="section-note">A high-level view of the collected repository records.</p>',
        unsafe_allow_html=True,
    )

    total_issues = issue_metrics.get("total_issues", 0)
    open_issues = issue_metrics.get("open_issues", 0)
    total_prs = pr_metrics.get("total_pull_requests", 0)
    open_prs = pr_metrics.get("open_pull_requests", 0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Issues", total_issues)
    col2.metric("Open Issues", open_issues)
    col3.metric("Total Pull Requests", total_prs)
    col4.metric("Open Pull Requests", open_prs)

    st.divider()
    st.subheader("Repository activity breakdown")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        make_state_chart(issues_df, "Issue status distribution")
    with chart_col2:
        make_state_chart(prs_df, "Pull request status distribution")

    st.divider()
    st.subheader("Issue health and resolution")
    st.markdown(
        '<p class="section-note">Track backlog risk and how long issues take to resolve.</p>',
        unsafe_allow_html=True,
    )

    issue_col1, issue_col2, issue_col3, issue_col4 = st.columns(4)
    issue_col1.metric(
        "Issue closure rate",
        f'{issue_metrics.get("issue_closure_rate", 0):.1f}%',
        help="Closed issues divided by all collected issues.",
    )
    issue_col2.metric(
        "Aging open issues",
        issue_metrics.get("aging_issues", 0),
        help="Open issues older than 30 days.",
    )
    issue_col3.metric(
        "Aging issue percentage",
        f'{issue_metrics.get("aging_issue_percentage", 0):.1f}%',
        help="Aging open issues divided by all open issues.",
    )
    issue_col4.metric(
        "Median resolution time",
        f'{issue_metrics.get("median_resolution_time_days", 0):.1f} days',
        help="Median time between issue creation and closure.",
    )

    st.caption(
        "Average and median resolution times use collected closed issues "
        "with valid creation and closure timestamps."
    )

    st.divider()
    st.subheader("Pull request health")
    pr_col1, pr_col2, pr_col3, pr_col4 = st.columns(4)

    pr_col1.metric(
        "PR closure rate",
        f'{pr_metrics.get("pr_closure_rate", 0):.1f}%',
    )

    if pr_metrics.get("merge_rate_available", False):
        pr_col2.metric(
            "PR merge rate",
            f'{pr_metrics.get("pr_merge_rate", 0):.1f}%',
        )
        pr_col3.metric(
            "Merged pull requests",
            pr_metrics.get("merged_pull_requests", 0),
        )
    else:
        pr_col2.metric("PR merge rate", "N/A")
        pr_col3.metric("Merged pull requests", "N/A")

    pr_col4.metric(
        "Median PR closing time",
        f'{pr_metrics.get("median_pr_closing_time_days", 0):.1f} days',
    )

    st.divider()
    st.subheader("Turnaround time analysis")
    st.markdown(
        '<p class="section-note">Compare average and median issue resolution and '
        'pull request closing durations. Lower values indicate shorter turnaround '
        'times for the records measured.</p>',
        unsafe_allow_html=True,
    )
    make_turnaround_chart(issue_metrics, pr_metrics)

    st.divider()
    st.subheader("Pull request merge analysis")
    make_merge_chart(pr_metrics, chart_key="overview_merge_chart")

    st.divider()
    st.subheader("Repository health observations")
    observation_col1, observation_col2 = st.columns(2)

    with observation_col1:
        with st.container(border=True):
            st.markdown("### Issue backlog")
            aging_count = issue_metrics.get("aging_issues", 0)
            aging_percentage = issue_metrics.get("aging_issue_percentage", 0)

            st.metric("Open issues older than 30 days", aging_count)
            st.progress(
                min(max(aging_percentage / 100, 0), 1),
                text=f"{aging_percentage:.1f}% of open issues are aging",
            )

            if open_issues == 0:
                st.caption("There are no open issues in this dataset.")
            elif aging_count > 0:
                st.warning("Some open issues may need maintainer attention.")
            else:
                st.success("No open issues older than 30 days were identified.")

    with observation_col2:
        with st.container(border=True):
            st.markdown("### Pending pull requests")
            average_open_pr_age = pr_metrics.get("average_open_pr_age_days", 0)
            aging_open_prs = pr_metrics.get("aging_open_pull_requests", 0)
            aging_pr_percentage = pr_metrics.get("aging_open_pr_percentage", 0)

            st.metric(
                "Average age of open PRs",
                f"{average_open_pr_age:.1f} days",
            )
            st.metric("Open PRs older than 30 days", aging_open_prs)
            st.progress(
                min(max(aging_pr_percentage / 100, 0), 1),
                text=f"{aging_pr_percentage:.1f}% of open PRs are aging",
            )

            if open_prs == 0:
                st.caption("There are no open pull requests in the dataset.")
            elif aging_open_prs > 0:
                st.warning("Review older open pull requests for possible delays.")
            else:
                st.success(
                    "No open pull requests older than 30 days were identified."
                )

    st.divider()
    st.subheader("Collection summary")
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    summary_col1.metric("Issues collected", total_issues)
    summary_col2.metric("PRs collected", total_prs)
    summary_col3.metric("Total records", total_issues + total_prs)

    st.caption(
        "These insights describe the collected records, not necessarily the "
        "complete repository history. The collector currently retrieves a "
        "limited number of recent records."
    )


# ==================================================
# 11. ISSUES
# ==================================================

elif st.session_state["active_tab"] == "Issues":
    st.subheader("Issue backlog analysis")

    if not issues_df.empty:
        issue_col1, issue_col2, issue_col3, issue_col4 = st.columns(4)
        issue_col1.metric("Total Issues", issue_metrics.get("total_issues", 0))
        issue_col2.metric("Open Issues", issue_metrics.get("open_issues", 0))
        issue_col3.metric("Aging Issues", issue_metrics.get("aging_issues", 0))
        issue_col4.metric(
            "Closure Rate",
            f'{issue_metrics.get("issue_closure_rate", 0):.1f}%',
        )

        st.markdown("#### Resolution metrics")
        resolution_col1, resolution_col2 = st.columns(2)
        resolution_col1.metric(
            "Average resolution time",
            f'{issue_metrics.get("average_resolution_time_days", 0):.1f} days',
        )
        resolution_col2.metric(
            "Median resolution time",
            f'{issue_metrics.get("median_resolution_time_days", 0):.1f} days',
        )

        selected_state = st.selectbox(
            "Filter by issue status",
            ["All", "open", "closed"],
            key="issue_state_filter",
        )
        filtered_issues = issues_df.copy()

        if selected_state != "All" and "state" in filtered_issues.columns:
            filtered_issues = filtered_issues[
                filtered_issues["state"].astype(str).str.lower() == selected_state
            ]

        st.markdown("#### Collected issues")
        display_dataframe(filtered_issues, "No issues match the selected filter.")

        st.download_button(
            "Download issues as CSV",
            data=filtered_issues.to_csv(index=False).encode("utf-8"),
            file_name="issues.csv",
            mime="text/csv",
            key="download_issues",
        )
    else:
        show_empty_state(
            "No issue data available",
            "Fetch a repository from the sidebar to view issue metrics and the collected issue table.",
        )


# ==================================================
# 12. PULL REQUESTS
# ==================================================

elif st.session_state["active_tab"] == "Pull Requests":
    st.subheader("Pull request analysis")

    if not prs_df.empty:
        pr_col1, pr_col2, pr_col3, pr_col4 = st.columns(4)
        pr_col1.metric(
            "Total Pull Requests",
            pr_metrics.get("total_pull_requests", 0),
        )
        pr_col2.metric(
            "Open Pull Requests",
            pr_metrics.get("open_pull_requests", 0),
        )
        pr_col3.metric(
            "Closed Pull Requests",
            pr_metrics.get("closed_pull_requests", 0),
        )

        if pr_metrics.get("merge_rate_available", False):
            pr_col4.metric(
                "Merged Pull Requests",
                pr_metrics.get("merged_pull_requests", 0),
            )
        else:
            pr_col4.metric("Merged Pull Requests", "N/A")

        st.markdown("#### PR turnaround metrics")
        time_col1, time_col2, time_col3, time_col4 = st.columns(4)
        time_col1.metric(
            "Average closing time",
            f'{pr_metrics.get("average_pr_closing_time_days", 0):.1f} days',
        )
        time_col2.metric(
            "Median closing time",
            f'{pr_metrics.get("median_pr_closing_time_days", 0):.1f} days',
        )
        time_col3.metric(
            "Average age of open PRs",
            f'{pr_metrics.get("average_open_pr_age_days", 0):.1f} days',
        )
        time_col4.metric(
            "Aging open PRs",
            pr_metrics.get("aging_open_pull_requests", 0),
        )

        st.markdown("#### PR outcomes")
        make_merge_chart(pr_metrics, chart_key="pull_requests_merge_chart")

        selected_state = st.selectbox(
            "Filter by pull request status",
            ["All", "open", "closed"],
            key="pr_state_filter",
        )
        filtered_prs = prs_df.copy()

        if selected_state != "All" and "state" in filtered_prs.columns:
            filtered_prs = filtered_prs[
                filtered_prs["state"].astype(str).str.lower() == selected_state
            ]

        st.markdown("#### Collected pull requests")
        display_dataframe(filtered_prs, "No pull requests match the selected filter.")

        st.download_button(
            "Download pull requests as CSV",
            data=filtered_prs.to_csv(index=False).encode("utf-8"),
            file_name="pull_requests.csv",
            mime="text/csv",
            key="download_pull_requests",
        )

        st.caption(
            "Merge rate is calculated using pull requests with a merge timestamp "
            "divided by all collected PRs. Closure rate measures closed PRs "
            "divided by all collected PRs. These are different metrics. A closed "
            "PR may have been merged or closed without merging."
        )
    else:
        show_empty_state(
            "No pull request data available",
            "Fetch a repository from the sidebar to view pull request metrics and the collected pull request table.",
        )


# ==================================================
# 13. CONTRIBUTORS
# ==================================================

elif st.session_state["active_tab"] == "Contributors":
    st.subheader("Contributor activity")

    contributor_frames = []

    if not issues_df.empty and "user" in issues_df.columns:
        contributor_frames.append(
            issues_df[["user"]].rename(columns={"user": "contributor"})
        )

    if not prs_df.empty and "user" in prs_df.columns:
        contributor_frames.append(
            prs_df[["user"]].rename(columns={"user": "contributor"})
        )

    if contributor_frames:
        contributor_data = pd.concat(
            contributor_frames,
            ignore_index=True,
        ).dropna(subset=["contributor"])

        if not contributor_data.empty:
            contributor_summary = (
                contributor_data.groupby("contributor")
                .size()
                .reset_index(name="Collected Records")
                .sort_values("Collected Records", ascending=False)
            )

            st.caption(
                "Counts represent collected issue and pull request records, "
                "not every contribution made by each GitHub user."
            )

            chart = px.bar(
                contributor_summary.head(15),
                x="contributor",
                y="Collected Records",
                title="Most active contributors in collected records",
                text="Collected Records",
                color="Collected Records",
                color_continuous_scale=["#233A59", BLUE],
                template="plotly_dark",
            )
            chart.update_traces(
                textposition="outside",
                cliponaxis=False,
                marker_line_width=0,
            )
            chart.update_layout(
                height=400,
                paper_bgcolor=CARD_COLOR,
                plot_bgcolor="#111A2B",
                font=dict(
                    family="Inter, Segoe UI, Roboto, Arial, sans-serif",
                    color=TEXT_COLOR,
                    size=12,
                ),
                margin=dict(t=65, b=100, l=25, r=25),
                xaxis=dict(
                    title="Contributor",
                    tickangle=-35,
                    showgrid=False,
                ),
                yaxis=dict(
                    title="Collected records",
                    rangemode="tozero",
                    gridcolor=GRID_COLOR,
                ),
                coloraxis_showscale=False,
            )
            st.plotly_chart(
                chart,
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

            st.markdown("#### Contributor summary")
            display_dataframe(contributor_summary, "No contributor records are available.")

            st.download_button(
                "Download contributor summary",
                data=contributor_summary.to_csv(index=False).encode("utf-8"),
                file_name="contributors.csv",
                mime="text/csv",
                key="download_contributors",
            )
        else:
            show_empty_state(
                "No contributor usernames found",
                "The collected records do not contain contributor usernames.",
            )
    else:
        show_empty_state(
            "Contributor insights are not available yet",
            "Fetch repository data to analyze usernames appearing in issues and pull requests.",
        )


# ==================================================
# 14. FOOTER
# ==================================================

st.divider()
st.caption(
    "Open-Source Maintainer Insights Platform | "
    "Python • Pandas • SQLite • Streamlit • Plotly"
)