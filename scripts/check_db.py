import sqlite3

if __name__ == "__main__":
    conn = sqlite3.connect(r"C:\Users\1028120\AppData\Local\corp-by-os\overnight_state.db")
    tables = [
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    ]
    print("Tables:", tables)
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {count} rows")
        cols = [d[0] for d in conn.execute(f"SELECT * FROM [{t}] LIMIT 0").description]
        print(f"    cols: {cols}")
        if count > 0:
            row = conn.execute(f"SELECT * FROM [{t}] LIMIT 1").fetchone()
            print(f"    sample: {row}")
