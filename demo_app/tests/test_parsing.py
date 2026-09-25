import pytest

from demo_app.app.parsing import parse_user


def test_parse_user_normal():
    out = parse_user({"name": "Ada", "email": "ADA@example.com"})
    assert out == {"name": "Ada", "email": "ada@example.com"}


def test_parse_user_missing_email_is_graceful():
    # email is optional; a missing email should not crash.
    out = parse_user({"name": "Ada"})
    assert out["name"] == "Ada"
    assert out["email"] is None


def test_parse_user_null_email_is_graceful():
    out = parse_user({"name": "Ada", "email": None})
    assert out["email"] is None
