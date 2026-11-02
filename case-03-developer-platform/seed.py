import os
import time

import psycopg

url = os.environ["DATABASE_URL"]
for attempt in range(30):
    try:
        with psycopg.connect(url, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS preview_items (item_id integer PRIMARY KEY, label text NOT NULL, amount integer NOT NULL)")
                cur.executemany(
                    "INSERT INTO preview_items (item_id, label, amount) VALUES (%s, %s, %s) ON CONFLICT (item_id) DO UPDATE SET label=excluded.label, amount=excluded.amount",
                    [(1, "synthetic-basic", 10), (2, "synthetic-boundary", 0), (3, "synthetic-large", 999)],
                )
        print("seeded 3 deterministic synthetic rows")
        break
    except psycopg.OperationalError:
        if attempt == 29:
            raise
        time.sleep(1)
