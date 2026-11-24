from contextlib import contextmanager
from pathlib import Path
import re
import sqlite3
from config import Config

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(getattr(Config, "SQLITE_PATH", BASE_DIR / "consciouscart.db"))
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
SEED_PATH = BASE_DIR / "database" / "seed.sql"

_initialized = False


class _SQLiteCursorWrapper:
    def __init__(self, raw_cursor: sqlite3.Cursor, dictionary: bool = True):
        self._cur = raw_cursor
        self._dictionary = dictionary
        self.lastrowid = None
        self.rowcount = 0

    @staticmethod
    def _adapt_sql(sql: str) -> str:
        s = sql.strip().replace("`", "")
        s = s.replace("%s", "?")
        s = re.sub(r"\bCURDATE\s*\(\s*\)", "date('now')", s, flags=re.IGNORECASE)
        s = re.sub(r"\bNOW\s*\(\s*\)", "CURRENT_TIMESTAMP", s, flags=re.IGNORECASE)
        s = re.sub(r"\bTRUE\b", "1", s, flags=re.IGNORECASE)
        s = re.sub(r"\bFALSE\b", "0", s, flags=re.IGNORECASE)
        s = re.sub(r"\bINSERT\s+IGNORE\s+INTO\b", "INSERT OR IGNORE INTO", s, flags=re.IGNORECASE)

        dup_match = re.search(
            r"\bON\s+DUPLICATE\s+KEY\s+UPDATE\s+(.+)$",
            s,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if dup_match:
            update_clause = dup_match.group(1).strip().rstrip(";")
            update_clause = re.sub(
                r"VALUES\s*\(\s*([a-zA-Z0-9_]+)\s*\)",
                r"excluded.\1",
                update_clause,
                flags=re.IGNORECASE,
            )
            prefix = s[: dup_match.start()].strip()
            prefix = re.sub(
                r"\bINSERT\s+OR\s+IGNORE\s+INTO\b",
                "INSERT INTO",
                prefix,
                flags=re.IGNORECASE,
            )
            s = f"{prefix} ON CONFLICT DO UPDATE SET {update_clause}"

        return s

    def execute(self, sql: str, params=None):
        adapted = self._adapt_sql(sql)
        if params is None:
            self._cur.execute(adapted)
        else:
            self._cur.execute(adapted, tuple(params))
        self.lastrowid = self._cur.lastrowid
        self.rowcount = self._cur.rowcount
        return self

    def executemany(self, sql: str, seq_of_params):
        adapted = self._adapt_sql(sql)
        self._cur.executemany(adapted, [tuple(p) for p in seq_of_params])
        self.lastrowid = self._cur.lastrowid
        self.rowcount = self._cur.rowcount
        return self

    def _row_to_dict(self, row):
        if row is None or not self._dictionary:
            return row
        if isinstance(row, sqlite3.Row):
            return dict(row)
        cols = [d[0] for d in (self._cur.description or [])]
        return dict(zip(cols, row))

    def fetchone(self):
        return self._row_to_dict(self._cur.fetchone())

    def fetchall(self):
        rows = self._cur.fetchall()
        if not self._dictionary:
            return rows
        return [self._row_to_dict(r) for r in rows]

    def close(self):
        self._cur.close()


def _split_sql_statements(sql_text: str):
    statements = []
    buf = []
    in_single = False
    i = 0
    n = len(sql_text)
    while i < n:
        ch = sql_text[i]
        if ch == "'":
            if in_single and i + 1 < n and sql_text[i + 1] == "'":
                buf.append("''")
                i += 2
                continue
            in_single = not in_single
            buf.append(ch)
        elif ch == ";" and not in_single:
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def _clean_create_table_block(block: str) -> str:
    b = block.replace("`", "")
    b = re.sub(r"\)\s*ENGINE\s*=.*$", ")", b, flags=re.IGNORECASE | re.DOTALL)
    b = re.sub(r"\)\s*DEFAULT\s+CHARSET\s*=.*$", ")", b, flags=re.IGNORECASE | re.DOTALL)

    open_idx = b.find("(")
    close_idx = b.rfind(")")
    if open_idx == -1 or close_idx == -1:
        return b

    header = b[: open_idx + 1]
    body = b[open_idx + 1 : close_idx]
    footer = b[close_idx:]

    parts = []
    depth = 0
    in_single = False
    current = []
    for ch in body:
        if ch == "'":
            in_single = not in_single
            current.append(ch)
        elif not in_single:
            if ch == "(":
                depth += 1
                current.append(ch)
            elif ch == ")":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())

    cleaned_parts = []
    has_int_pk = False
    for part in parts:
        p = re.sub(r"\s+", " ", part).strip()
        if not p:
            continue
        upper = p.upper()
        if upper.startswith((
            "KEY ",
            "INDEX ",
            "UNIQUE KEY ",
            "UNIQUE INDEX ",
            "FULLTEXT ",
            "SPATIAL ",
            "CONSTRAINT ",
            "FOREIGN KEY ",
        )):
            continue

        if re.search(r"\bAUTO_INCREMENT\b", p, flags=re.IGNORECASE):
            col_name = p.split()[0]
            cleaned_parts.append(f"{col_name} INTEGER PRIMARY KEY AUTOINCREMENT")
            has_int_pk = True
            continue

        p = re.sub(
            r"\bBIGINT\b|\bMEDIUMINT\b|\bSMALLINT\b|\bTINYINT\b",
            "INTEGER",
            p,
            flags=re.IGNORECASE,
        )
        p = re.sub(r"\bINT\b", "INTEGER", p, flags=re.IGNORECASE)
        p = re.sub(r"\bUNSIGNED\b", "", p, flags=re.IGNORECASE)
        p = re.sub(r"\bENUM\s*\([^)]+\)", "TEXT", p, flags=re.IGNORECASE)
        p = re.sub(r"\bDATETIME\b|\bTIMESTAMP\b", "TEXT", p, flags=re.IGNORECASE)
        p = re.sub(r"\bDOUBLE\b|\bFLOAT\b", "REAL", p, flags=re.IGNORECASE)
        p = re.sub(
            r"\bON\s+UPDATE\s+CURRENT_TIMESTAMP(\(\d*\))?",
            "",
            p,
            flags=re.IGNORECASE,
        )
        p = re.sub(r"\bCOMMENT\s+'[^']*'", "", p, flags=re.IGNORECASE)
        p = re.sub(r"\bCHARACTER\s+SET\s+\w+", "", p, flags=re.IGNORECASE)
        p = re.sub(r"\bCOLLATE\s+\w+", "", p, flags=re.IGNORECASE)
        p = re.sub(r"\s+", " ", p).strip()

        if upper.startswith("PRIMARY KEY") and has_int_pk:
            continue

        cleaned_parts.append(p)

    return f"{header} {', '.join(cleaned_parts)} {footer}"


def _sql_script_to_sqlite(sql_text: str, make_inserts_ignore: bool = False) -> str:
    no_block_comments = re.sub(r"/\*.*?\*/", "", sql_text, flags=re.DOTALL)
    lines = []
    for line in no_block_comments.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        upper = stripped.upper()
        if upper.startswith((
            "CREATE DATABASE",
            "USE ",
            "SET ",
            "LOCK TABLES",
            "UNLOCK TABLES",
            "DELIMITER",
            "ALTER TABLE",
        )):
            continue
        lines.append(line)

    script = "\n".join(lines).replace("`", "")
    script = re.sub(r"\bCURDATE\s*\(\s*\)", "date('now')", script, flags=re.IGNORECASE)
    script = re.sub(r"\bNOW\s*\(\s*\)", "CURRENT_TIMESTAMP", script, flags=re.IGNORECASE)
    script = re.sub(r"\bTRUE\b", "1", script, flags=re.IGNORECASE)
    script = re.sub(r"\bFALSE\b", "0", script, flags=re.IGNORECASE)
    script = re.sub(r"\bINSERT\s+IGNORE\s+INTO\b", "INSERT OR IGNORE INTO", script, flags=re.IGNORECASE)
    if make_inserts_ignore:
        script = re.sub(r"\bINSERT\s+INTO\b", "INSERT OR IGNORE INTO", script, flags=re.IGNORECASE)

    cleaned_statements = []
    for stmt in _split_sql_statements(script):
        if re.match(r"^CREATE\s+(TEMPORARY\s+)?TABLE\b", stmt, flags=re.IGNORECASE):
            stmt = _clean_create_table_block(stmt)
        cleaned_statements.append(stmt)

    return ";\n".join(cleaned_statements)


def _deduplicate_certifications(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organic_certifications'")
    if cur.fetchone() is None:
        return
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(organic_certifications)").fetchall()]
    if "id" not in cols or "product_id" not in cols:
        return
    name_col = next(
        (c for c in ["certifier_name", "certification_name", "name", "cert_name", "status"] if c in cols),
        None,
    )
    if name_col:
        conn.execute(
            f"""
            DELETE FROM organic_certifications
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM organic_certifications
                GROUP BY product_id, COALESCE({name_col}, '')
            )
            """
        )
    else:
        conn.execute(
            """
            DELETE FROM organic_certifications
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM organic_certifications
                GROUP BY product_id
            )
            """
        )


def init_db():
    global _initialized
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = OFF;")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        has_products = cur.fetchone() is not None

        if not has_products and SCHEMA_PATH.exists():
            schema_sql = _sql_script_to_sqlite(
                SCHEMA_PATH.read_text(encoding="utf-8", errors="ignore"),
                make_inserts_ignore=False,
            )
            for s in _split_sql_statements(schema_sql):
                try:
                    conn.execute(s)
                except sqlite3.OperationalError as exc:
                    print(f"[SQLite Schema Warning] {exc} -> {s[:120]}")

        if SEED_PATH.exists():
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
            if cur.fetchone() is not None:
                p_count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
                if p_count == 0:
                    seed_sql = _sql_script_to_sqlite(
                        SEED_PATH.read_text(encoding="utf-8", errors="ignore"),
                        make_inserts_ignore=True,
                    )
                    for s in _split_sql_statements(seed_sql):
                        try:
                            conn.execute(s)
                        except sqlite3.Error as exc:
                            print(f"[SQLite Seed Warning] {exc} -> {s[:120]}")

        _deduplicate_certifications(conn)
        conn.commit()
        _initialized = True
    finally:
        conn.close()


@contextmanager
def get_db_cursor(dictionary=True):
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    wrapper = _SQLiteCursorWrapper(conn.cursor(), dictionary=dictionary)
    try:
        yield wrapper
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        wrapper.close()
        conn.close()