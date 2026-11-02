import asyncio
import os
import secrets
from random import uniform

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

STABLE_URL = os.getenv("STABLE_URL", "http://stable:8000")
CANARY_URL = os.getenv("CANARY_URL", "http://canary:8000")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "local-demo-token")
canary_percent = int(os.getenv("CANARY_PERCENT", "5"))
weight_lock = asyncio.Lock()
app = FastAPI(title="Incident recovery lab router", docs_url=None, redoc_url=None)
ROUTED = Counter("portfolio_router_requests_total", "Requests routed by upstream", ["upstream"])
WEIGHT = Gauge("portfolio_router_canary_percent", "Current configured canary traffic percentage")
WEIGHT.set(canary_percent)
TOTAL_SLOTS = asyncio.Semaphore(25)
LOW_PRIORITY_SLOTS = asyncio.Semaphore(15)
LOAD_SHED = Counter(
    "portfolio_router_load_shed_total",
    "Requests rejected at the router before reaching an upstream",
    ["priority", "status"],
)
client: httpx.AsyncClient | None = None


class WeightUpdate(BaseModel):
    percent: int = Field(ge=0, le=100)


@app.on_event("startup")
async def startup():
    global client
    client = httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=1.0))


@app.on_event("shutdown")
async def shutdown():
    if client:
        await client.aclose()


@app.get("/health")
async def health():
    return {"status": "ok", "canary_percent": canary_percent}


@app.get("/admin/canary")
async def get_weight():
    return {"canary_percent": canary_percent}


@app.post("/admin/canary")
async def set_weight(update: WeightUpdate, x_admin_token: str = Header(default="")):
    global canary_percent
    if not secrets.compare_digest(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(status_code=403, detail="admin token required")
    async with weight_lock:
        canary_percent = update.percent
        WEIGHT.set(canary_percent)
    return {"canary_percent": canary_percent}


@app.api_route("/api/{path:path}", methods=["GET", "POST"])
async def proxy(path: str, request: Request):
    if client is None:
        raise HTTPException(status_code=503, detail="router is starting")
    priority = request.query_params.get("priority", "low")
    low_acquired = False
    total_acquired = False
    if priority != "critical":
        if LOW_PRIORITY_SLOTS.locked():
            LOAD_SHED.labels(priority, "429").inc()
            raise HTTPException(
                status_code=429,
                detail="router low-priority capacity is full",
                headers={"Retry-After": "1", "X-Load-Shed": "true"},
            )
        await LOW_PRIORITY_SLOTS.acquire()
        low_acquired = True
    if TOTAL_SLOTS.locked():
        if low_acquired:
            LOW_PRIORITY_SLOTS.release()
        LOAD_SHED.labels(priority, "503").inc()
        raise HTTPException(
            status_code=503,
            detail="router is shedding load",
            headers={"Retry-After": "1", "X-Load-Shed": "true"},
        )
    await TOTAL_SLOTS.acquire()
    total_acquired = True
    try:
        destination = "canary" if uniform(0, 100) < canary_percent else "stable"
        base_url = CANARY_URL if destination == "canary" else STABLE_URL
        ROUTED.labels(destination).inc()
        upstream = f"{base_url}/api/{path}"
        try:
            upstream_response = await client.request(
                request.method,
                upstream,
                params=request.query_params,
                content=await request.body(),
                headers={key: value for key, value in request.headers.items() if key.lower() not in {"host", "content-length"}},
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"upstream unavailable: {destination}") from exc
        headers = {key: value for key, value in upstream_response.headers.items() if key.lower() not in {"content-length", "transfer-encoding", "connection"}}
        headers["X-Upstream"] = destination
        return Response(content=upstream_response.content, status_code=upstream_response.status_code, headers=headers)
    finally:
        if total_acquired:
            TOTAL_SLOTS.release()
        if low_acquired:
            LOW_PRIORITY_SLOTS.release()


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
