"""3-screen streaming demo server.

Screen 1: paste a trace.  Screen 2: the hypothesis race + Granite ranking live.
Screen 3: verdict card + triage timer.

Events are pushed over Server-Sent Events (SSE) as the triage pipeline hits each milestone, so
the UI reflects the REAL orchestration order (race -> rank -> critic -> fix).

Run:  python -m ui.server   then open http://127.0.0.1:8000
"""
import asyncio
import json
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from orchestrator import config
from orchestrator.triage import stream_triage

app = FastAPI(title="Culprit — triage demo")
_HERE = os.path.dirname(__file__)


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(_HERE, "static", "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/config")
def cfg():
    """Lets the UI show whether it's running against real Bob (LIVE) or canned data (MOCK)."""
    return {"mock": config.MOCK_MODE}


@app.post("/triage")
async def triage(request: Request):
    body = await request.json()
    trace = body.get("trace", "")

    async def gen():
        queue: asyncio.Queue = asyncio.Queue()

        def emit(kind, payload):
            queue.put_nowait({"kind": kind, "payload": payload})

        async def run():
            try:
                await stream_triage(trace, emit=emit)
            finally:
                queue.put_nowait(None)  # sentinel

        task = asyncio.create_task(run())
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
        await task

    return StreamingResponse(gen(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
