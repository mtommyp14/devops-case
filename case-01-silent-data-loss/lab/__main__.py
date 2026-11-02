import argparse
import json
import os
import time

import psycopg
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from kafka.structs import OffsetAndMetadata, TopicPartition
from prometheus_client import Gauge, start_http_server
from .domain import adapt_event, build_events, validate_event

SOURCE_TOPIC = os.getenv("SOURCE_TOPIC", "consent-events")
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
DB = os.getenv("DATABASE_URL", "postgresql://lab:lab-local-only@localhost:5432/consent_lab")

SCHEMA = """
CREATE TABLE IF NOT EXISTS source_ledger (
  event_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  source_schema TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS consent_sink (
  run_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  customer_id TEXT NOT NULL,
  consent BOOLEAN NOT NULL,
  recovered BOOLEAN NOT NULL DEFAULT false,
  written_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (run_id, event_id)
);
CREATE TABLE IF NOT EXISTS quarantine (
  run_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','recovered')),
  quarantined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (run_id, event_id)
);
"""


def db_connect():
    return psycopg.connect(DB)


def wait_db():
    for _ in range(60):
        try:
            with db_connect() as conn:
                conn.execute("SELECT 1")
            return
        except psycopg.OperationalError:
            time.sleep(1)
    raise RuntimeError("PostgreSQL did not become available")


def wait_kafka():
    for _ in range(60):
        try:
            producer = KafkaProducer(bootstrap_servers=BOOTSTRAP, request_timeout_ms=2000)
            producer.close()
            return
        except NoBrokersAvailable:
            time.sleep(1)
    raise RuntimeError("Kafka did not become available")


def init_db():
    wait_db()
    with db_connect() as conn:
        for statement in SCHEMA.split(";"):
            if statement.strip():
                conn.execute(statement)


def seed(args):
    init_db()
    wait_kafka()
    events = build_events(args.count)
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP,
                             value_serializer=lambda obj: json.dumps(obj).encode("utf-8"),
                             key_serializer=lambda key: key.encode("utf-8"),
                             acks="all", retries=5)
    for event in events:
        # Commit the source record before publishing, so the ledger remains a
        # useful reconciliation reference if Kafka publishing fails midway.
        with db_connect() as conn:
            conn.execute("INSERT INTO source_ledger(event_id,payload,source_schema) VALUES (%s,%s,%s) ON CONFLICT(event_id) DO NOTHING",
                         (event["event_id"], json.dumps(event), str(event["schema_version"])))
        producer.send(SOURCE_TOPIC, key=event["event_id"], value=event).get(timeout=15)
    producer.flush()
    producer.close()
    print(json.dumps({"seeded": len(events), "source_topic": SOURCE_TOPIC,
                      "schema_drift_ids": [e["event_id"] for e in events if "consent_v2" in e]}, indent=2))


def process_event(conn, event, mode, run_id):
    event_id = event["event_id"]
    consent, reason = validate_event(event)
    if reason and mode == "broken":
        # Reproduce the silent bug: acknowledge the record while dropping it.
        return "silently_dropped"
    elif reason and mode == "hardened":
        conn.execute("INSERT INTO quarantine(run_id,event_id,payload,reason) VALUES (%s,%s,%s,%s) ON CONFLICT(run_id,event_id) DO NOTHING",
                     (run_id, event_id, json.dumps(event), reason))
        return "quarantined"
    elif mode not in ("broken", "hardened"):
        raise ValueError("mode must be broken or hardened")

    conn.execute("INSERT INTO consent_sink(run_id,event_id,customer_id,consent) VALUES (%s,%s,%s,%s) ON CONFLICT(run_id,event_id) DO NOTHING",
                 (run_id, event_id, event["customer_id"], consent))
    return "delivered"


def worker(args):
    init_db()
    consumer = KafkaConsumer(SOURCE_TOPIC, bootstrap_servers=BOOTSTRAP,
                             group_id=args.group_id, enable_auto_commit=False,
                             auto_offset_reset="earliest", consumer_timeout_ms=30000,
                             session_timeout_ms=10000, heartbeat_interval_ms=3000,
                             value_deserializer=lambda raw: json.loads(raw.decode("utf-8")))
    counts = {"delivered": 0, "quarantined": 0, "silently_dropped": 0}
    try:
        for message in consumer:
            with db_connect() as conn:
                outcome = process_event(conn, message.value, args.mode, args.run_id)
            counts[outcome] += 1
            if args.crash_after_sink_once and outcome == "delivered":
                # Deliberately exit after the DB transaction, before committing this Kafka offset.
                os._exit(17)
            # Commit only this successfully accounted record. A consumer may
            # prefetch later offsets, which must not be acknowledged early.
            partition = TopicPartition(message.topic, message.partition)
            consumer.commit({partition: OffsetAndMetadata(message.offset + 1, "", message.leader_epoch)})
            if args.once and len(counts) and sum(counts.values()) >= args.count:
                break
    finally:
        consumer.close()
    print(json.dumps({"run_id": args.run_id, "mode": args.mode, **counts}, indent=2))


def report(args):
    init_db()
    with db_connect() as conn:
        source = conn.execute("SELECT count(*) FROM source_ledger").fetchone()[0]
        delivered = conn.execute("SELECT count(*) FROM consent_sink WHERE run_id=%s", (args.run_id,)).fetchone()[0]
        pending = conn.execute("SELECT count(*) FROM quarantine WHERE run_id=%s AND status='pending'", (args.run_id,)).fetchone()[0]
        q_total = conn.execute("SELECT count(*) FROM quarantine WHERE run_id=%s", (args.run_id,)).fetchone()[0]
        duplicates = conn.execute("SELECT count(*) FROM (SELECT event_id FROM consent_sink WHERE run_id=%s GROUP BY event_id HAVING count(*)>1) d", (args.run_id,)).fetchone()[0]
        unaccounted = conn.execute("SELECT count(*) FROM source_ledger l WHERE NOT EXISTS (SELECT 1 FROM consent_sink s WHERE s.run_id=%s AND s.event_id=l.event_id) AND NOT EXISTS (SELECT 1 FROM quarantine q WHERE q.run_id=%s AND q.event_id=l.event_id AND q.status='pending')", (args.run_id, args.run_id)).fetchone()[0]
        missing = conn.execute("SELECT COALESCE(json_agg(l.event_id ORDER BY l.event_id),'[]'::json) FROM source_ledger l WHERE NOT EXISTS (SELECT 1 FROM consent_sink s WHERE s.run_id=%s AND s.event_id=l.event_id) AND NOT EXISTS (SELECT 1 FROM quarantine q WHERE q.run_id=%s AND q.event_id=l.event_id AND q.status='pending')", (args.run_id, args.run_id)).fetchone()[0]
        orphan_sink = conn.execute("SELECT count(*) FROM consent_sink s WHERE s.run_id=%s AND NOT EXISTS (SELECT 1 FROM source_ledger l WHERE l.event_id=s.event_id)", (args.run_id,)).fetchone()[0]
        lag = conn.execute("SELECT max(EXTRACT(EPOCH FROM (s.written_at-l.created_at))) FROM consent_sink s JOIN source_ledger l USING(event_id) WHERE s.run_id=%s", (args.run_id,)).fetchone()[0]
    print(json.dumps({"run_id": args.run_id, "source_count": source, "delivered_count": delivered,
                      "quarantined_pending_count": pending, "quarantined_total_count": q_total,
                      "unaccounted_count": unaccounted, "unaccounted_ids": missing,
                      "orphan_sink_count": orphan_sink,
                      "duplicate_sink_record_count": duplicates,
                      "max_source_to_sink_lag_seconds": float(lag) if lag is not None else None,
                      "health_check": "green (process liveness only; delivery requires reconciliation)"}, indent=2))


def recover(args):
    init_db()
    recovered = 0
    with db_connect() as conn:
        rows = conn.execute("SELECT event_id,payload FROM quarantine WHERE run_id=%s AND status='pending' ORDER BY event_id", (args.run_id,)).fetchall()
        for event_id, payload in rows:
            event = payload if isinstance(payload, dict) else json.loads(payload)
            consent, reason = adapt_event(event)
            if reason:
                continue
            conn.execute("INSERT INTO consent_sink(run_id,event_id,customer_id,consent,recovered) VALUES (%s,%s,%s,%s,true) ON CONFLICT(run_id,event_id) DO NOTHING",
                         (args.run_id, event_id, event["customer_id"], consent))
            conn.execute("UPDATE quarantine SET status='recovered' WHERE run_id=%s AND event_id=%s", (args.run_id, event_id))
            recovered += 1
    print(json.dumps({"run_id": args.run_id, "recovered": recovered,
                      "adapter": "consent_v2 -> consent", "repeat_safe": True}, indent=2))


def metrics_server(args):
    init_db()
    delivered = Gauge("consent_lab_delivered_events", "Sink events by demo run", ["run_id"])
    quarantined = Gauge("consent_lab_pending_quarantine_events", "Pending quarantine events by demo run", ["run_id"])
    unaccounted = Gauge("consent_lab_unaccounted_events", "Source events with no sink or pending quarantine record", ["run_id"])
    freshness = Gauge("consent_lab_max_source_to_sink_lag_seconds", "Maximum source-ledger to sink write lag in seconds", ["run_id"])
    source_count = Gauge("consent_lab_source_events", "Source ledger events")
    start_http_server(args.port)
    while True:
        try:
            with db_connect() as conn:
                source = conn.execute("SELECT count(*) FROM source_ledger").fetchone()[0]
                source_count.set(source)
                runs = conn.execute("SELECT run_id FROM consent_sink UNION SELECT run_id FROM quarantine").fetchall()
                for (run_id,) in runs:
                    d = conn.execute("SELECT count(*) FROM consent_sink WHERE run_id=%s", (run_id,)).fetchone()[0]
                    q = conn.execute("SELECT count(*) FROM quarantine WHERE run_id=%s AND status='pending'", (run_id,)).fetchone()[0]
                    unaccounted_count = conn.execute("SELECT count(*) FROM source_ledger l WHERE NOT EXISTS (SELECT 1 FROM consent_sink s WHERE s.run_id=%s AND s.event_id=l.event_id) AND NOT EXISTS (SELECT 1 FROM quarantine q WHERE q.run_id=%s AND q.event_id=l.event_id AND q.status='pending')", (run_id, run_id)).fetchone()[0]
                    lag = conn.execute("SELECT max(EXTRACT(EPOCH FROM (s.written_at-l.created_at))) FROM consent_sink s JOIN source_ledger l USING(event_id) WHERE s.run_id=%s", (run_id,)).fetchone()[0]
                    delivered.labels(run_id).set(d)
                    quarantined.labels(run_id).set(q)
                    unaccounted.labels(run_id).set(unaccounted_count)
                    freshness.labels(run_id).set(float(lag or 0))
        except psycopg.OperationalError:
            pass
        time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Synthetic schema-drift reliability lab")
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("seed"); s.add_argument("--count", type=int, default=20); s.set_defaults(func=seed)
    w = sub.add_parser("worker"); w.add_argument("--mode", choices=["broken", "hardened"], required=True)
    w.add_argument("--run-id", required=True); w.add_argument("--group-id", required=True)
    w.add_argument("--once", action="store_true"); w.add_argument("--count", type=int, default=20)
    w.add_argument("--crash-after-sink-once", action="store_true"); w.set_defaults(func=worker)
    r = sub.add_parser("report"); r.add_argument("--run-id", required=True); r.set_defaults(func=report)
    q = sub.add_parser("recover"); q.add_argument("--run-id", required=True); q.set_defaults(func=recover)
    m = sub.add_parser("metrics"); m.add_argument("--port", type=int, default=int(os.getenv("METRICS_PORT", "8000"))); m.set_defaults(func=metrics_server)
    h = sub.add_parser("help"); h.set_defaults(func=lambda _: parser.print_help())
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
