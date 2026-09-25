"""Runs the parallel hypothesis race — N subagents, each on a different angle, concurrently."""
import asyncio
import sys
from typing import List, Optional

from . import config
from .bob_shell import run_bob_task, parse_json
from .prompts import load_prompt
from .schema import Hypothesis

# The angles the race spreads across. In real mode `angle` is injected into the prompt; in mock
# mode the `id` selects the canned reply for the detected scenario (see bob_shell._SCENARIOS).
ANGLES = [
    {"id": "h1", "angle": "Logic error in the code path named by the trace "
                          "(off-by-one, boundary, wrong operator, missing await)."},
    {"id": "h2", "angle": "Input validation / unhandled edge case (missing/None/empty input)."},
    {"id": "h3", "angle": "Data / state / configuration issue (seed data, shared state, env)."},
]


async def _run_one(spec: dict, trace: str) -> Optional[Hypothesis]:
    prompt = load_prompt("hypothesis_agent").format(angle=spec["angle"], trace=trace)
    try:
        # run_bob_task is blocking (subprocess); push it off the event loop.
        raw = await asyncio.to_thread(run_bob_task, prompt, role=spec["id"], scenario_text=trace)
        data = parse_json(raw)
        return Hypothesis(
            id=spec["id"],
            title=data["title"],
            culprit_file=data["culprit_file"],
            culprit_symbol=data["culprit_symbol"],
            line_hint=data.get("line_hint"),
            reasoning=data["reasoning"],
            confidence=float(data.get("confidence", 0.5)),
        )
    except Exception as e:
        # One flaky/empty agent must not kill the whole race — drop it and carry on.
        print(f"[hypothesis {spec['id']} failed: {type(e).__name__}: {e}]", file=sys.stderr)
        return None


async def run_race(trace: str) -> List[Hypothesis]:
    specs = ANGLES[: config.RACE_WIDTH]
    results = await asyncio.gather(*[_run_one(s, trace) for s in specs])
    return [h for h in results if h is not None]
