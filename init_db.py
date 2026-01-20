import sqlite3
import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "cell-count.csv"
DB_PATH = BASE_DIR / "cell_counts.db"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cell_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    subject TEXT NOT NULL,
    condition TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    treatment TEXT NOT NULL,
    response TEXT,
    sample TEXT NOT NULL,
    sample_type TEXT NOT NULL,
    time_from_treatment_start INTEGER NOT NULL,
    b_cell INTEGER NOT NULL,
    cd8_t_cell INTEGER NOT NULL,
    cd4_t_cell INTEGER NOT NULL,
    nk_cell INTEGER NOT NULL,
    monocyte INTEGER NOT NULL
);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    # Return rows as dict-like objects if needed later
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute("DROP TABLE IF EXISTS cell_counts;")
        conn.execute(SCHEMA_SQL)


def load_csv_into_db(conn: sqlite3.Connection, csv_path: Path) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row["project"],
                row["subject"],
                row["condition"],
                int(row["age"]),
                row["sex"],
                row["treatment"],
                row.get("response") or None,
                row["sample"],
                row["sample_type"],
                int(row["time_from_treatment_start"]),
                int(row["b_cell"]),
                int(row["cd8_t_cell"]),
                int(row["cd4_t_cell"]),
                int(row["nk_cell"]),
                int(row["monocyte"]),
            )
            for row in reader
        ]

    with conn:
        conn.executemany(
            """
            INSERT INTO cell_counts (
                project,
                subject,
                condition,
                age,
                sex,
                treatment,
                response,
                sample,
                sample_type,
                time_from_treatment_start,
                b_cell,
                cd8_t_cell,
                cd4_t_cell,
                nk_cell,
                monocyte
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            rows,
        )


def main() -> None:
    print(f"Using CSV: {CSV_PATH}")
    print(f"Creating database at: {DB_PATH}")

    conn = get_connection(DB_PATH)
    try:
        init_db(conn)
        load_csv_into_db(conn, CSV_PATH)
    finally:
        conn.close()

    print("Database initialization complete.")


if __name__ == "__main__":
    main()
