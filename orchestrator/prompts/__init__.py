"""Prompt loader — prompts live as .md files next to this module so they're easy to edit."""
import os

_HERE = os.path.dirname(__file__)


def load_prompt(name: str) -> str:
    path = os.path.join(_HERE, f"{name}.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
