from demo_app.app.pagination import paginate


def test_first_page_returns_first_items():
    items = list(range(1, 101))
    # 1-indexed: page 1 should be the first 10 items.
    assert paginate(items, page=1, per_page=10) == list(range(1, 11))


def test_second_page():
    items = list(range(1, 101))
    assert paginate(items, page=2, per_page=10) == list(range(11, 21))
