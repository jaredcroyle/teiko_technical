import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path("cell_counts.db")

# Teiko-inspired color palette (from teiko-labs.com)
TEIKO_RED = "#FF4B4B"        # bright red
TEIKO_NAVY = "#050816"       # dark navy background
TEIKO_NAVY_SOFT = "#111827"  # soft dark navy for contrast


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load all data from the SQLite database into a DataFrame.
    If the DB file or table is missing, return an empty DataFrame.
    """
    # If DB file doesn't exist, return empty DataFrame
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cell_counts'"
        )
        if cur.fetchone() is None:
            # table not found
            return pd.DataFrame()
        df = pd.read_sql_query("SELECT * FROM cell_counts", conn)
    except Exception:
        # Any DB error -> return empty DataFrame to let main() handle messaging
        return pd.DataFrame()
    finally:
        conn.close()
    return df


def set_page_style() -> None:
    st.set_page_config(
        page_title="Teiko-style Immune Dashboard",
        layout="wide",
    )
    st.markdown(
        f"""
        <style>
            body {{
                background-color: {TEIKO_NAVY};
                color: #FFFFFF;
            }}
            .stApp {{
                background-color: {TEIKO_NAVY};
                color: #FFFFFF;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #FFFFFF;
            }}
            .css-18e3th9, .css-1d391kg {{
                background-color: {TEIKO_NAVY_SOFT};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_sample_db(path: Path = DB_PATH) -> None:
    """Create a small sample cell_counts.db with a cell_counts table for demo/testing."""
    import sqlite3
    sample = pd.DataFrame(
        [
            {
                "project": "P1",
                "subject": "S1",
                "sample": "SM1",
                "condition": "healthy",
                "treatment": "A",
                "response": "responder",
                "sample_type": "PBMC",
                "time_from_treatment_start": 0,
                "b_cell": 100,
            },
            {
                "project": "P1",
                "subject": "S1",
                "sample": "SM2",
                "condition": "healthy",
                "treatment": "A",
                "response": "non-responder",
                "sample_type": "PBMC",
                "time_from_treatment_start": 7,
                "b_cell": 80,
            },
            {
                "project": "P1",
                "subject": "S2",
                "sample": "SM3",
                "condition": "disease",
                "treatment": "B",
                "response": "responder",
                "sample_type": "PBMC",
                "time_from_treatment_start": 14,
                "b_cell": 150,
            },
            {
                "project": "P2",
                "subject": "S3",
                "sample": "SM4",
                "condition": "disease",
                "treatment": "B",
                "response": "non-responder",
                "sample_type": "tissue",
                "time_from_treatment_start": 7,
                "b_cell": 60,
            },
        ]
    )
    conn = sqlite3.connect(path)
    try:
        sample.to_sql("cell_counts", conn, index=False, if_exists="replace")
    finally:
        conn.close()


def main() -> None:
    set_page_style()
    st.title("Immune Cell Population Dashboard")

    df = load_data()

    # If no data (missing DB/file/table or error), show message and allow creating a demo DB
    if df.empty:
        if not DB_PATH.exists():
            st.warning(f"Database file not found: {DB_PATH.resolve()}")
            st.info("You can create a small demo database so the dashboard can run.")
            if st.button("Create sample database (demo)"):
                create_sample_db()
                st.success(f"Created sample database at {DB_PATH.resolve()}. Reloading...")
                st.experimental_rerun()
            st.caption(
                "Or run locally: pip install streamlit pandas plotly && "
                f"streamlit run {DB_PATH.parent / 'dashboard.py'}"
            )
            return
        else:
            st.error(
                f"Database table 'cell_counts' not found in {DB_PATH.resolve()}. "
                "Ensure the SQLite file exists and contains a table named 'cell_counts'."
            )
            st.info(
                "If you need a quick test dataset, create the database or provide a CSV and import it. "
                "Example SQL to check tables: SELECT name FROM sqlite_master WHERE type='table';"
            )
            return

    st.sidebar.header("Filters")
    conditions = sorted(df["condition"].dropna().unique())
    treatments = sorted(df["treatment"].dropna().unique())
    sample_types = sorted(df["sample_type"].dropna().unique())
    timepoints_all = sorted(df["time_from_treatment_start"].dropna().unique())

    selected_conditions = st.sidebar.multiselect(
        "Condition", conditions, default=conditions
    )
    selected_treatments = st.sidebar.multiselect(
        "Treatment", treatments, default=treatments
    )
    selected_sample_types = st.sidebar.multiselect(
        "Sample type", sample_types, default=["PBMC"] if "PBMC" in sample_types else sample_types
    )
    selected_timepoints = st.sidebar.multiselect(
        "Time from treatment start", timepoints_all
    )

    mask = (
        df["condition"].isin(selected_conditions)
        & df["treatment"].isin(selected_treatments)
        & df["sample_type"].isin(selected_sample_types)
        & (
            df["time_from_treatment_start"].isin(selected_timepoints)
            if selected_timepoints
            else True
        )
    )
    filtered = df[mask]

    st.subheader("Sample Overview")
    st.write(
        filtered[
            [
                "project",
                "subject",
                "sample",
                "condition",
                "treatment",
                "response",
                "sample_type",
                "time_from_treatment_start",
            ]
        ].head(20)
    )

    st.subheader("B cell counts over time by response (PBMC)")
    pbmc = filtered[filtered["sample_type"] == "PBMC"]
    if not pbmc.empty:
        fig = px.box(
            pbmc,
            x="time_from_treatment_start",
            y="b_cell",
            color="response",
            color_discrete_sequence=[TEIKO_RED, TEIKO_NAVY_SOFT],
            labels={
                "time_from_treatment_start": "Days from treatment start",
                "b_cell": "B cell count",
                "response": "Response",
            },
            title="B cell counts over time (PBMC)",
        )
        fig.update_layout(
            paper_bgcolor=TEIKO_NAVY_SOFT,
            plot_bgcolor=TEIKO_NAVY_SOFT,
            font_color="#FFFFFF",
            legend_title_font_color="#FFFFFF",
            legend_font_color="#FFFFFF",
        )
        fig.update_traces(marker_line_color="#FFFFFF")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No PBMC data for the current filter selection.")


if __name__ == "__main__":
    main()
