"""watsonx.ai Granite ranker: scores hypotheses by risk / blast-radius.

Granite-first is rewarded by the hackathon guide (and some non-IBM models are penalized), so the
ranking stage runs on a Granite model. MOCK_MODE returns a deterministic ranking; real mode calls
watsonx.ai via REST (text generation) — verify the endpoint/payload against current IBM docs.
"""
import json
from typing import List

import requests

from . import config
from .schema import Hypothesis, RankedHypothesis
from .prompts import load_prompt


def rank(hypotheses: List[Hypothesis], trace_summary: str) -> List[RankedHypothesis]:
    if config.MOCK_MODE:
        return _mock_rank(hypotheses)
    if not (config.WATSONX_API_KEY and config.WATSONX_PROJECT_ID):
        # watsonx not configured yet — fall back to the heuristic ranker so the Bob agent
        # pipeline can still run end-to-end. Wire watsonx creds to enable real Granite ranking.
        return _mock_rank(hypotheses)
    return _granite_rank(hypotheses, trace_summary)


def _mock_rank(hypotheses: List[Hypothesis]) -> List[RankedHypothesis]:
    ranked = []
    for h in hypotheses:
        # risk = confidence, nudged up when it names a concrete file+symbol+line.
        specificity = 1.0 if (h.culprit_symbol and h.line_hint) else 0.6
        risk = round(min(1.0, h.confidence * 0.7 + specificity * 0.3), 3)
        reason = ("Directly and fully explains the observed failure, with a concrete "
                  "file/symbol/line."
                  if h.confidence >= 0.7 else
                  "Only partially explains the failure, or lacks a concrete location.")
        ranked.append(RankedHypothesis(hypothesis=h, risk_score=risk, rank_reason=reason))
    ranked.sort(key=lambda r: r.risk_score, reverse=True)
    return ranked


def _granite_rank(hypotheses: List[Hypothesis], trace_summary: str) -> List[RankedHypothesis]:
    if not (config.WATSONX_API_KEY and config.WATSONX_PROJECT_ID):
        raise RuntimeError("watsonx.ai credentials missing; set WATSONX_* in .env or use MOCK_MODE=1")

    token = _iam_token(config.WATSONX_API_KEY)
    prompt = load_prompt("granite_rank").format(
        trace_summary=trace_summary,
        hypotheses_json=json.dumps([h.to_dict() for h in hypotheses], indent=2),
    )
    # TODO: verify the current watsonx.ai text-generation endpoint + version param.
    url = f"{config.WATSONX_URL}/ml/v1/text/generation?version=2024-05-01"
    payload = {
        "model_id": config.GRANITE_MODEL_ID,
        "project_id": config.WATSONX_PROJECT_ID,
        "input": prompt,
        "parameters": {"decoding_method": "greedy", "max_new_tokens": 700},
    }
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload, timeout=60)
    resp.raise_for_status()
    text = resp.json()["results"][0]["generated_text"]
    scored = _extract_json_array(text)  # expect [{"id":..,"risk_score":..,"rank_reason":..}, ...]

    by_id = {h.id: h for h in hypotheses}
    ranked = [
        RankedHypothesis(hypothesis=by_id[s["id"]], risk_score=float(s["risk_score"]),
                         rank_reason=s["rank_reason"])
        for s in scored if s["id"] in by_id
    ]
    ranked.sort(key=lambda r: r.risk_score, reverse=True)
    return ranked


def _extract_json_array(text: str) -> list:
    """Pull the JSON array out of Granite's output, tolerating fences and surrounding prose."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            head, rest = text.split("\n", 1)
            if head.strip().lower() in ("json", ""):
                text = rest
        text = text.strip()
    idx = text.find("[")
    if idx == -1:
        raise ValueError(f"no JSON array in Granite output: {text[:200]}")
    arr, _ = json.JSONDecoder().raw_decode(text[idx:])
    return arr


def _iam_token(api_key: str) -> str:
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]
