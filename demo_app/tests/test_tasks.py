import pytest

from demo_app.app.tasks import process_task


@pytest.mark.asyncio
async def test_process_task_returns_enriched_dict():
    result = await process_task({"id": 1, "title": "task-1"})
    # Must be the enriched dict, not a coroutine.
    assert isinstance(result, dict)
    assert result.get("enriched") is True
    assert result["id"] == 1
