"""Request payload parsing."""
from typing import Dict


def parse_user(payload: Dict) -> Dict:
    return {
        "name": payload["name"],
        "email": payload["email"].lower(),
    }
