import asyncio
import json
import os
import time

import psycopg
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

RELEASE = os.getenv("APP_RELEASE", "unknown")
FAULT = os.getenv("APP_FAULT", "none")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lab:lab-local-only@postgres:5432/incident_lab")
TOTAL_SLOTS = asyncio.Semaphore(25)
LOW_PRIORITY_SLOTS = asyncio.Semaphore(15)

REQUESTS = Counter("portfolio_requests_total", "Requests served or load-shed by a lab release", ["release", "status", "outcome"])
LATENCY = Histogram(
    "portfolio_request_duration_seconds",
    "Application request latency",
    ["release"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1, 2, 5),
)
DB_LATENCY = Histogram("portfolio_db_query_seconds", "Synthetic database query latency", ["release"])

app = FastAPI(title="Incident recovery lab service", docs_url=None, redoc_url=None)


@app.middleware("http")
async def measure_request(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started
    if request.url.path.startswith("/api/"):
        shed = response.headers.get("X-Load-Shed") == "true"
        outcome = "load_shed" if shed else "served"
        REQUESTS.labels(RELEASE, str(response.status_code), outcome).inc()
        if not shed:
            LATENCY.labels(RELEASE).observe(elapsed)
        response.headers["X-Release"] = RELEASE
        print(json.dumps({"event": "request", "release": RELEASE, "path": request.url.path, "priority": request.query_params.get("priority", "low"), "status": response.status_code, "duration_seconds": round(elapsed, 6)}), flush=True)
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "release": RELEASE}


@app.get("/api/work")
async def work(request: Request):
    priority = request.query_params.get("priority", "low")
    low_acquired = False
    try:
        if priority != "critical":
            try:
                await asyncio.wait_for(LOW_PRIORITY_SLOTS.acquire(), timeout=0.01)
                low_acquired = True
            except TimeoutError:
                raise HTTPException(status_code=429, detail="low-priority capacity is full", headers={"Retry-After": "1", "X-Load-Shed": "true"})
        try:
            await asyncio.wait_for(TOTAL_SLOTS.acquire(), timeout=0.02)
        except TimeoutError:
            raise HTTPException(status_code=503, detail="service is shedding load", headers={"Retry-After": "1", "X-Load-Shed": "true"})
        try:
            if FAULT == "error":
                raise HTTPException(status_code=503, detail="synthetic canary failure")
            if FAULT == "slow":
                await asyncio.sleep(0.35)
            db_delay = 0.35 if FAULT == "db-slow" else 0
            db_started = time.perf_counter()
            async with await psycopg.AsyncConnection.connect(DATABASE_URL, connect_timeout=2) as connection:
                async with connection.cursor() as cursor:
                    if db_delay:
                        await cursor.execute("SELECT pg_sleep(%s)", (db_delay,))
                    await cursor.execute("SELECT 1")
                    row = await cursor.fetchone()
            DB_LATENCY.labels(RELEASE).observe(time.perf_counter() - db_started)
            return {"release": RELEASE, "result": row[0], "priority": priority, "fault": FAULT}
        finally:
            TOTAL_SLOTS.release()
    finally:
        if low_acquired:
            LOW_PRIORITY_SLOTS.release()


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
