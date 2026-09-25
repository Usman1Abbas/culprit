"""Adversarial critic: tries to disprove the top-ranked hypothesis before it's shown."""
import asyncio
import json

from .bob_shell import run_bob_task, parse_json
from .prompts import load_prompt
from .schema import RankedHypothesis, CriticVerdict


async def challenge(top: RankedHypothesis, trace: str) -> CriticVerdict:
    prompt = load_prompt("critic_agent").format(
        hypothesis_json=json.dumps(top.hypothesis.to_dict(), indent=2),
        trace=trace,
    )
    raw = await asyncio.to_thread(run_bob_task, prompt, role="critic", scenario_text=trace)
    data = parse_json(raw)
    return CriticVerdict(
        disproof_test=data["disproof_test"],
        disproved=bool(data["disproved"]),
        verdict_reason=data["verdict_reason"],
    )
