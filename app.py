from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.api.data_collector import (
    collect_repository_data,
    save_repository_data,
)
from src.database.db import save_to_database
from src.analytics.metrics import (
    calculate_issue_metrics,
    calculate_pr_metrics,
)


# ==================================================
# 1. APPLICATION CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ISSUES_FILE = DATA_DIR / "issues.csv"
PRS_FILE = DATA_DIR / "pull_requests.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Maintainer Insights Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# 2. PROFESSIONAL DARK DASHBOARD STYLING
# ==================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0B1120;
        color: #E5EDF8;
    }

    [data-testid="stHeader"] {
        background: rgba(11, 17, 32, 0.85);
    }

    [data-testid="stSidebar"] {
        background: #10192A;
        border-right: 1px solid #26344A;
    }

    [data-testid="stSidebar"] * {
        color: #E5EDF8;
    }

    [data-testid="stSidebar"] input {
        background: #151F32 !important;
        color: #E5EDF8 !important;
        border-color: #34445D !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #151F32;
        border-color: #34445D;
    }

    .hero {
        background: linear-gradient(
            120deg,
            #172554 0%,
            #15365C 55%,
            #164E63 100%
        );
        padding: 30px;
        border: 1px solid #2B4B73;
        border-radius: 16px;
        color: #F8FAFC;
        margin-bottom: 24px;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
    }

    .hero h1 {
        color: #F8FAFC;
        font-size: 30px;
        font-weight: 750;
        margin: 0 0 10px 0;
    }

    .hero p {
        color: #D3E3F7;
        font-size: 15px;
        line-height: 1.7;
        margin: 0;
    }

    .section-note {
        color: #9AABC2;
        font-size: 14px;
        line-height: 1.6;
    }

    div[data-testid="stMetric"] {
        background: #151F32;
        border: 1px solid #293951;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
    }

    div[data-testid="stMetricLabel"] {
        color: #9AABC2;
    }

    div[data-testid="stMetricValue"] {
        color: #F1F5F9;
        font-weight: 700;
    }

    div[data-testid="stMetricDelta"] {
        font-weight: 600;
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
        min-height: 40px;
        transition: border-color 0.15s ease;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        border-color: #60A5FA;
        color: #93C5FD;
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

    h1, h2, h3 {
        color: #F1F5F9;
    }

    hr {
        border-color: #293951;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# 3. DATA LOADING AND HELPER FUNCTIONS
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
    """Display a data table or an informative empty state."""

    if dataframe.empty:
        st.info(message)
    else:
        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True,
        )


def make_state_chart(dataframe, title):
    """Display a dark-themed bar chart showing record status."""

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

    if chart_data.empty:
        st.info(f"No records are available for {title.lower()}.")
        return

    figure = px.bar(
        chart_data,
        x="Status",
        y="Records",
        color="Status",
        text="Records",
        title=title,
        color_discrete_map={
            "Open": "#60A5FA",
            "Closed": "#34D399",
            "Unknown": "#94A3B8",
        },
        template="plotly_dark",
    )

    figure.update_traces(
        textposition="outside",
        textfont=dict(
            color="#E5EDF8",
            size=12,
        ),
        cliponaxis=False,
        marker_line_width=0,
    )

    figure.update_layout(
        height=350,
        autosize=True,
        paper_bgcolor="#151F32",
        plot_bgcolor="#111A2B",
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color="#E5EDF8",
        ),
        title=dict(
            text=title,
            font=dict(
                size=18,
                color="#F1F5F9",
            ),
            x=0.03,
            xanchor="left",
        ),
        showlegend=False,
        margin=dict(
            t=65,
            b=45,
            l=35,
            r=25,
        ),
        xaxis=dict(
            title="Status",
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            tickfont=dict(color="#CBD5E1"),
        ),
        yaxis=dict(
            title="Number of records",
            rangemode="tozero",
            gridcolor="#293951",
            zerolinecolor="#293951",
            fixedrange=True,
            tickfont=dict(color="#CBD5E1"),
        ),
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        config={"displayModeBar": False},
        theme=None,
    )


def show_empty_state(title, description):
    """Display a helpful message when a section has no data."""

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.write(description)


# ==================================================
# 4. SIDEBAR AND GITHUB REPOSITORY SELECTION
# ==================================================

with st.sidebar:
    st.markdown("## 📊 Maintainer Insights")
    st.caption("Open-source repository analytics")
    st.divider()

    st.markdown("### GitHub repository")

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
        "🔄 Fetch latest GitHub data",
        use_container_width=True,
        type="primary",
    )

    st.divider()

    st.markdown("### About this platform")
    st.caption(
        "Analyze issue backlogs, pull requests, and contributor "
        "participation using GitHub repository data."
    )

    st.markdown("**Data source:** GitHub REST API")
    st.markdown("**Data storage:** CSV + SQLite")


# ==================================================
# 5. FETCH AND SAVE DATA
# ==================================================

if fetch_clicked:
    if not owner.strip() or not repo.strip():
        st.sidebar.error(
            "Please enter both the repository owner and repository name."
        )
    else:
        try:
            with st.spinner(
                f"Fetching {owner.strip()}/{repo.strip()}..."
            ):
                new_issues, new_prs = collect_repository_data(
                    owner.strip(),
                    repo.strip(),
                )

                save_repository_data(
                    new_issues,
                    new_prs,
                )

                save_to_database(
                    owner.strip(),
                    repo.strip(),
                    new_issues,
                    new_prs,
                )

            st.session_state["last_fetched_repo"] = (
                f"{owner.strip()}/{repo.strip()}"
            )

            st.session_state["fetch_success"] = (
                f"Successfully fetched {len(new_issues)} issues and "
                f"{len(new_prs)} pull requests from "
                f"{owner.strip()}/{repo.strip()}. "
                "CSV files and SQLite database updated."
            )

            load_csv_data.clear()
            st.rerun()

        except Exception as error:
            st.sidebar.error(
                "Could not fetch or save repository data. "
                "Check the repository name, internet connection, "
                "and GitHub API availability."
            )
            st.sidebar.caption(f"Details: {error}")


# ==================================================
# 6. DASHBOARD HEADER
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
# 7. LOAD SAVED DATA
# ==================================================

issues_df = load_csv_data(ISSUES_FILE)
prs_df = load_csv_data(PRS_FILE)

if issues_df.empty and prs_df.empty:
    show_empty_state(
        "Welcome to Maintainer Insights",
        "No repository records have been loaded yet. "
        "Choose a public GitHub repository in the sidebar and "
        "click 'Fetch latest GitHub data' to populate the dashboard.",
    )


# ==================================================
# 8. DASHBOARD TABS
# ==================================================

overview_tab, issues_tab, prs_tab, contributors_tab = st.tabs(
    [
        "📈 Overview",
        "🐛 Issues",
        "🔀 Pull Requests",
        "👥 Contributors",
    ]
)


# ==================================================
# 9. OVERVIEW
# ==================================================

with overview_tab:
    st.subheader("Repository overview")

    st.markdown(
        '<p class="section-note">'
        "A high-level view of the collected repository records."
        "</p>",
        unsafe_allow_html=True,
    )

    issue_metrics = calculate_issue_metrics(issues_df)
    pr_metrics = calculate_pr_metrics(prs_df)

    total_issues = issue_metrics.get("total_issues", 0)
    open_issues = issue_metrics.get("open_issues", 0)
    total_prs = pr_metrics.get("total_pull_requests", 0)
    open_prs = pr_metrics.get("open_pull_requests", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Issues",
            total_issues,
            help="Number of issue records currently collected.",
        )

    with col2:
        st.metric(
            "Open Issues",
            open_issues,
            help="Issues that are currently open in the collected data.",
        )

    with col3:
        st.metric(
            "Total Pull Requests",
            total_prs,
            help="Number of pull request records currently collected.",
        )

    with col4:
        st.metric(
            "Open Pull Requests",
            open_prs,
            help="Pull requests that are currently open in the collected data.",
        )

    st.divider()
    st.subheader("Repository activity breakdown")

    st.markdown(
        '<p class="section-note">'
        "Compare open and closed records in the data collected so far."
        "</p>",
        unsafe_allow_html=True,
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        make_state_chart(
            issues_df,
            "Issue status distribution",
        )

    with chart_col2:
        make_state_chart(
            prs_df,
            "Pull request status distribution",
        )

    st.divider()
    st.subheader("Key observations")

    st.markdown(
        '<p class="section-note">'
        "Quick insights to help maintainers identify potential bottlenecks."
        "</p>",
        unsafe_allow_html=True,
    )

    aging_count = issue_metrics.get("aging_issues", 0)
    average_age = pr_metrics.get("average_open_pr_age_days", 0)

    observation_col1, observation_col2 = st.columns(2)

    with observation_col1:
        with st.container(border=True):
            st.markdown("### 🐛 Issue backlog")

            st.metric(
                "Aging open issues",
                aging_count,
                help="Open issues older than 30 days.",
            )

            progress_value = (
                min(aging_count / open_issues, 1.0)
                if open_issues > 0
                else 0.0
            )

            st.progress(
                progress_value,
                text=(
                    f"{aging_count} of {open_issues} open issues "
                    "are older than 30 days"
                ),
            )

            if open_issues == 0:
                st.caption(
                    "There are currently no open issues in the collected data."
                )
            elif aging_count > 0:
                st.caption(
                    "Some open issues may need maintainer attention."
                )
            else:
                st.caption(
                    "No open issues older than 30 days were identified "
                    "in the collected records."
                )

    with observation_col2:
        with st.container(border=True):
            st.markdown("### 🔀 Pull request turnaround")

            st.metric(
                "Average age of open PRs",
                f"{average_age:.1f} days",
                help=(
                    "Average age of open pull requests in the collected data. "
                    "This is not the same as time to merge."
                ),
            )

            if open_prs == 0:
                st.caption(
                    "There are currently no open pull requests in the "
                    "collected data."
                )
            elif average_age >= 30:
                st.caption(
                    "The average open PR age is at least 30 days. "
                    "Review the PR backlog for potential delays."
                )
            else:
                st.caption(
                    "Use this metric to monitor the age of pending "
                    "pull requests over time."
                )

    st.divider()
    st.subheader("Collection summary")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric("Issues collected", total_issues)

    with summary_col2:
        st.metric("PRs collected", total_prs)

    with summary_col3:
        st.metric("Total records", total_issues + total_prs)

    st.caption(
        "These insights describe the collected records, not necessarily "
        "the complete history of the repository. The collector currently "
        "retrieves a limited number of recent records."
    )


# ==================================================
# 10. ISSUES
# ==================================================

with issues_tab:
    st.subheader("Issue backlog analysis")

    if not issues_df.empty:
        issue_metrics = calculate_issue_metrics(issues_df)

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Issues",
            issue_metrics.get("total_issues", 0),
        )

        col2.metric(
            "Open Issues",
            issue_metrics.get("open_issues", 0),
        )

        col3.metric(
            "Aging Issues",
            issue_metrics.get("aging_issues", 0),
        )

        if "state" in issues_df.columns:
            selected_state = st.selectbox(
                "Filter by issue status",
                ["All", "open", "closed"],
                key="issue_state_filter",
            )

            filtered_issues = issues_df.copy()

            if selected_state != "All":
                filtered_issues = filtered_issues[
                    filtered_issues["state"].astype(str).str.lower()
                    == selected_state
                ]
        else:
            filtered_issues = issues_df.copy()

        st.markdown("#### Collected issues")

        display_dataframe(
            filtered_issues,
            "No issues match the selected filter.",
        )

        st.download_button(
            "⬇️ Download issues as CSV",
            data=filtered_issues.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="issues.csv",
            mime="text/csv",
            key="download_issues",
        )

    else:
        show_empty_state(
            "No issue data available",
            "Fetch a repository from the sidebar to view issue metrics "
            "and the collected issue table.",
        )


# ==================================================
# 11. PULL REQUESTS
# ==================================================

with prs_tab:
    st.subheader("Pull request analysis")

    if not prs_df.empty:
        pr_metrics = calculate_pr_metrics(prs_df)

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Pull Requests",
            pr_metrics.get("total_pull_requests", 0),
        )

        col2.metric(
            "Open Pull Requests",
            pr_metrics.get("open_pull_requests", 0),
        )

        col3.metric(
            "Closed Pull Requests",
            pr_metrics.get("closed_pull_requests", 0),
        )

        if "state" in prs_df.columns:
            selected_state = st.selectbox(
                "Filter by pull request status",
                ["All", "open", "closed"],
                key="pr_state_filter",
            )

            filtered_prs = prs_df.copy()

            if selected_state != "All":
                filtered_prs = filtered_prs[
                    filtered_prs["state"].astype(str).str.lower()
                    == selected_state
                ]
        else:
            filtered_prs = prs_df.copy()

        st.markdown("#### Collected pull requests")

        display_dataframe(
            filtered_prs,
            "No pull requests match the selected filter.",
        )

        st.download_button(
            "⬇️ Download pull requests as CSV",
            data=filtered_prs.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="pull_requests.csv",
            mime="text/csv",
            key="download_pull_requests",
        )

        st.caption(
            "A closed pull request may be merged or closed without merging. "
            "This dashboard currently tracks open and closed states only."
        )

    else:
        show_empty_state(
            "No pull request data available",
            "Fetch a repository from the sidebar to view pull request metrics "
            "and the collected pull request table.",
        )


# ==================================================
# 12. CONTRIBUTORS
# ==================================================

with contributors_tab:
    st.subheader("Contributor activity")

    contributor_frames = []

    if not issues_df.empty and "user" in issues_df.columns:
        issue_users = issues_df[["user"]].copy()
        issue_users = issue_users.rename(
            columns={"user": "contributor"}
        )
        contributor_frames.append(issue_users)

    if not prs_df.empty and "user" in prs_df.columns:
        pr_users = prs_df[["user"]].copy()
        pr_users = pr_users.rename(
            columns={"user": "contributor"}
        )
        contributor_frames.append(pr_users)

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
                .sort_values(
                    "Collected Records",
                    ascending=False,
                )
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
                color_continuous_scale=[
                    "#233A59",
                    "#60A5FA",
                ],
                template="plotly_dark",
            )

            chart.update_traces(
                textposition="outside",
                textfont=dict(color="#E5EDF8"),
                cliponaxis=False,
                marker_line_width=0,
            )

            chart.update_layout(
                height=400,
                paper_bgcolor="#151F32",
                plot_bgcolor="#111A2B",
                font=dict(
                    family="Arial, sans-serif",
                    color="#E5EDF8",
                    size=12,
                ),
                title=dict(
                    font=dict(
                        size=18,
                        color="#F1F5F9",
                    ),
                    x=0.03,
                    xanchor="left",
                ),
                margin=dict(
                    t=65,
                    b=100,
                    l=25,
                    r=25,
                ),
                xaxis=dict(
                    title="Contributor",
                    tickangle=-35,
                    showgrid=False,
                    tickfont=dict(color="#CBD5E1"),
                ),
                yaxis=dict(
                    title="Collected records",
                    rangemode="tozero",
                    gridcolor="#293951",
                    zerolinecolor="#293951",
                    tickfont=dict(color="#CBD5E1"),
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

            display_dataframe(
                contributor_summary,
                "No contributor records are available.",
            )

            st.download_button(
                "⬇️ Download contributor summary",
                data=contributor_summary.to_csv(
                    index=False
                ).encode("utf-8"),
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
            "Fetch repository data to analyze usernames appearing in issues "
            "and pull requests.",
        )


# ==================================================
# 13. FOOTER
# ==================================================

st.divider()

st.caption(
    "Open-Source Maintainer Insights Platform | "
    "Python • Pandas • SQLite • Streamlit • Plotly"
)