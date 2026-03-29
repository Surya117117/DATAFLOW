import sqlite3
import os
import io
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_columns(conn):
    try:
        row = conn.execute("SELECT value FROM meta WHERE key='columns'").fetchone()
        if row:
            return row[0].split(",")
    except Exception:
        pass
    try:
        cursor = conn.execute("PRAGMA table_info(data_table)")
        cols = [r[1] for r in cursor.fetchall() if r[1] != "id"]
        return cols
    except Exception:
        return []


def get_columns():
    try:
        conn = get_connection()
        cols = _get_columns(conn)
        meta = {}
        try:
            rows = conn.execute("SELECT key, value FROM meta").fetchall()
            meta = {r[0]: r[1] for r in rows}
        except Exception:
            pass
        conn.close()
        return {
            "columns": cols,
            "filename": meta.get("filename", ""),
            "row_count": int(meta.get("row_count", 0))
        }
    except Exception:
        return {"columns": [], "filename": "", "row_count": 0}


def fetch_data(page: int, page_size: int, sort_col: str = None, sort_dir: str = "asc"):
    try:
        conn = get_connection()
        cols = _get_columns(conn)
        if not cols:
            return {"data": [], "total": 0, "page": page, "page_size": page_size, "columns": []}

        total = conn.execute("SELECT COUNT(*) FROM data_table").fetchone()[0]
        offset = (page - 1) * page_size

        order_clause = ""
        if sort_col and sort_col in cols:
            direction = "DESC" if sort_dir.lower() == "desc" else "ASC"
            order_clause = f'ORDER BY "{sort_col}" {direction}'

        col_select = ", ".join([f'"{c}"' for c in cols])
        rows = conn.execute(
            f"SELECT {col_select} FROM data_table {order_clause} LIMIT ? OFFSET ?",
            (page_size, offset)
        ).fetchall()

        conn.close()
        return {
            "data": [dict(zip(cols, row)) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "columns": cols
        }
    except Exception as e:
        return {
            "data": [], "total": 0, "page": page,
            "page_size": page_size, "columns": [], "error": str(e)
        }


def search_data(q: str, page: int, page_size: int, col_filter: str = None):
    try:
        conn = get_connection()
        cols = _get_columns(conn)
        if not cols:
            return {"data": [], "total": 0, "page": page, "page_size": page_size, "columns": []}

        search_term = f"%{q}%"

        if col_filter and col_filter in cols:
            where = f'"{col_filter}" LIKE ?'
            params_count = [search_term]
            params_fetch = [search_term, page_size, (page - 1) * page_size]
        else:
            conditions = " OR ".join([f'"{c}" LIKE ?' for c in cols])
            where = conditions
            params_count = [search_term] * len(cols)
            params_fetch = [search_term] * len(cols) + [page_size, (page - 1) * page_size]

        total = conn.execute(
            f"SELECT COUNT(*) FROM data_table WHERE {where}", params_count
        ).fetchone()[0]

        col_select = ", ".join([f'"{c}"' for c in cols])
        rows = conn.execute(
            f"SELECT {col_select} FROM data_table WHERE {where} LIMIT ? OFFSET ?",
            params_fetch
        ).fetchall()

        conn.close()
        return {
            "data": [dict(zip(cols, row)) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "columns": cols,
            "query": q
        }
    except Exception as e:
        return {
            "data": [], "total": 0, "page": page,
            "page_size": page_size, "columns": [], "error": str(e)
        }


def download_csv(q: str = None, col_filter: str = None) -> str:
    try:
        conn = get_connection()
        cols = _get_columns(conn)
        if not cols:
            return ""

        if q:
            search_term = f"%{q}%"
            if col_filter and col_filter in cols:
                where = f'WHERE "{col_filter}" LIKE ?'
                params = [search_term]
            else:
                conditions = " OR ".join([f'"{c}" LIKE ?' for c in cols])
                where = f"WHERE {conditions}"
                params = [search_term] * len(cols)
        else:
            where = ""
            params = []

        col_select = ", ".join([f'"{c}"' for c in cols])
        rows = conn.execute(
            f"SELECT {col_select} FROM data_table {where}", params
        ).fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cols)
        for row in rows:
            writer.writerow(list(row))

        return output.getvalue()
    except Exception:
        return ""
