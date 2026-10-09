
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# Store the database inside the project's data folder.
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = "sqlite:///data/maintainer_insights.db"
engine = create_engine(DATABASE_URL)


def initialize_database():
    """Create database tables if they do not exist."""
    with engine.begin() as connection:
        for table in ("issues", "pull_requests"):
            connection.execute(
                text(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        repository_owner TEXT NOT NULL,
                        repository_name TEXT NOT NULL,
                        number INTEGER NOT NULL,
                        title TEXT,
                        state TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        username TEXT,
                        PRIMARY KEY (
                            repository_owner,
                            repository_name,
                            number
                        )
                    )
                """)
            )


def save_to_database(owner, repo, issues_df, prs_df):
    """Replace stored records for this repository with fresh records."""
    initialize_database()

    tables = [
        ("issues", issues_df),
        ("pull_requests", prs_df),
    ]

    with engine.begin() as connection:
        for table, dataframe in tables:
            connection.execute(
                text(f"""
                    DELETE FROM {table}
                    WHERE repository_owner = :owner
                      AND repository_name = :repo
                """),
                {"owner": owner, "repo": repo},
            )

            records = dataframe.astype(object).where(
                pd.notna(dataframe), None
            ).to_dict(orient="records")

            if not records:
                continue

            database_records = [
                {
                    "repository_owner": owner,
                    "repository_name": repo,
                    "number": record["number"],
                    "title": record["title"],
                    "state": record["state"],
                    "created_at": record["created_at"],
                    "updated_at": record["updated_at"],
                    "username": record["user"],
                }
                for record in records
            ]

            connection.execute(
                text(f"""
                    INSERT INTO {table} (
                        repository_owner,
                        repository_name,
                        number,
                        title,
                        state,
                        created_at,
                        updated_at,
                        username
                    )
                    VALUES (
                        :repository_owner,
                        :repository_name,
                        :number,
                        :title,
                        :state,
                        :created_at,
                        :updated_at,
                        :username
                    )
                """),
                database_records,
            )


def get_record_counts():
    """Return the number of records stored in each table."""
    initialize_database()

    with engine.connect() as connection:
        issues = connection.execute(
            text("SELECT COUNT(*) FROM issues")
        ).scalar_one()

        prs = connection.execute(
            text("SELECT COUNT(*) FROM pull_requests")
        ).scalar_one()

    return {"issues": issues, "pull_requests": prs}


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")
    print("Database location: data/maintainer_insights.db")
    print("Stored records:", get_record_counts())