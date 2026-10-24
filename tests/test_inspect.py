import sqlite3

conn = sqlite3.connect(':memory:')
with open('dataset/evidence/databases/customer_data_read_replica_20260921.sql', encoding='utf-8') as f:
    conn.executescript(f.read())

tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print('Tables in evidence_05:', tables)

for t in tables:
    if t != 'snapshot_scope':
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})")]
        print(f"\n-- {t} (cols: {cols}) --")
        for r in conn.execute(f"SELECT * FROM {t} WHERE resource_id IN ('account_994', 'search_1007', 'search_8911', 'analytics_4440')").fetchall():
            print("  ", r)
