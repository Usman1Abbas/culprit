"""Central config. Reads .env if present; safe defaults keep everything in MOCK_MODE."""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv optional
    pass


def _bool(name: str, default: str = "1") -> bool:
    return os.getenv(name, default).strip() not in ("0", "false", "False", "")


# Master switch: 1 = canned agent output (zero Bobcoins), 0 = real Bob Shell + Granite.
MOCK_MODE = _bool("MOCK_MODE", "1")

# How many parallel hypothesis subagents run the race. Keep at 3 to protect the 40-Bobcoin budget.
RACE_WIDTH = int(os.getenv("RACE_WIDTH", "3"))

# Bob Shell (real mode).
# Auth is via the BOB_API_KEY env var (Scope = Inference), created from INSIDE the
# ibm-coding-challenge-uat instance. There is NO --instance flag: the instance is baked into
# the key. The key is picked up from the environment automatically.
#
# We invoke bob.js directly with node instead of the `bob` shim, because on Windows `bob`
# resolves to a .ps1/.cmd wrapper that Python's subprocess cannot launch directly.
BOB_NODE = os.getenv("BOB_NODE", "node")
BOB_JS = os.getenv(
    "BOB_JS",
    os.path.expandvars(r"%APPDATA%\npm\node_modules\bobshell\dist\bob.js"),
)
BOB_API_KEY = os.getenv("BOB_API_KEY", "")
BOB_TEAM_ID = os.getenv("BOB_TEAM_ID", "")   # required ONLY if the key type is 'general', not 'Inference'
BOB_MODE = os.getenv("BOB_MODE", "agent")    # agent | plan | ask
# Per-call Bobcoin ceiling — hard budget guard (you have 40 total for the whole hackathon).
BOB_MAX_COST = os.getenv("BOB_MAX_COST", "1.0")

# watsonx.ai Granite (real mode)
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
# Granite text-generation model available on watsonx (us-south, verified 2026-09-26).
# The older ibm/granite-3-8b-instruct id is deprecated/removed.
GRANITE_MODEL_ID = os.getenv("GRANITE_MODEL_ID", "ibm/granite-4-h-small")

# Repo the triage engine reasons about (the "patient").
REPO_ROOT = os.getenv("REPO_ROOT", os.path.join(os.path.dirname(__file__), "..", "demo_app"))

# Non-destructive triage: run agents against a throwaway COPY of the repo so they can never
# modify the real working tree (Bob agent mode has write tools that WILL edit code otherwise).
# On by default in real mode; irrelevant in mock mode.
SANDBOX = os.getenv("SANDBOX", "1").strip() not in ("0", "false", "False", "")
