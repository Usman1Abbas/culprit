"""Pagination helpers for the tasks API."""
from typing import List


def paginate(items: List, page: int, per_page: int) -> List:
    start = page * per_page
    end = start + per_page
    return items[start:end]
