import pandas as pd
import sqlite3
import io
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def process_upload(contents: bytes, filename: str) -> dict:
    """Parse file, clean it, store in SQLite, rebuild indexes."""
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(contents), dtype=str)
    except Exception as e:
        raise ValueError(f"Could not parse file: {str(e)}")


    df.columns = [
        str(c).strip().replace(" ", "_").replace("/", "_")
                .replace("(", "").replace(")", "").replace(".", "_").lower()
        for c in df.columns
    ]

    df.dropna(how="all", inplace=True)
    df.fillna("", inplace=True)

    if df.empty:
        raise ValueError("File has no data rows.")
    if len(df.columns) == 0:
        raise ValueError("File has no columns.")

    rows, cols = df.shape

    conn = get_connection()
    try:
        conn.execute("DROP TABLE IF EXISTS data_table")
        conn.execute("DROP TABLE IF EXISTS meta")
        conn.commit()

        df.columns = ['row_id' if c == 'id' else c for c in df.
                      columns]

        col_defs = ", ".join([f'"{c}" TEXT' for c in df.columns])
        conn.execute(

            f"CREATE TABLE data_table (_row_id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})"
)

        chunk_size = 1000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            placeholders = ", ".join(["?" for _ in df.columns])
            col_names = ", ".join([f'"{c}"' for c in df.columns])
            conn.executemany(
                f"INSERT INTO data_table ({col_names}) VALUES ({placeholders})",
                chunk.values.tolist()
            )

        for col in list(df.columns)[:10]:
            safe = col.replace('"', '').replace("'", "")
            try:
                conn.execute(
                    f'CREATE INDEX IF NOT EXISTS "idx_{safe}" ON data_table ("{col}")'
                )
            except Exception:
                pass

        conn.execute(
            "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('columns', ?)",
            [",".join(df.columns.tolist())]
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('filename', ?)", [filename]
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('row_count', ?)", [str(rows)]
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "success": True,
        "message": "File uploaded successfully!",
        "rows": rows,
        "columns": cols,
        "column_names": df.columns.tolist(),
        "filename": filename
    }
