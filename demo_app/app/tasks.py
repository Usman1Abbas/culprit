"""Async task processing."""
import asyncio
from typing import Dict


async def enrich(task: Dict) -> Dict:
    await asyncio.sleep(0)
    return {**task, "enriched": True}


async def process_task(task: Dict) -> Dict:
    result = enrich(task)
    return result
