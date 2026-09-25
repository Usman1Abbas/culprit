"""CLI entry: run triage on a trace file or inline string.

    python run_demo.py --trace samples/sample_trace_pagination.txt
    python run_demo.py --text "IndexError ... /tasks?page=1 returned items 11-20"
"""
import argparse
import asyncio
import sys

# Granite/Bob output can contain non-ASCII (e.g. non-breaking hyphens); avoid cp1252 crashes on Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from orchestrator.triage import run_triage


def _print_card(card):
    c = card.to_dict()
    print("\n" + "=" * 68)
    print("  CULPRIT — root-cause triage")
    print("=" * 68)
    print(f"Trace: {c['trace_summary']}")
    print(f"\nTriage time: {c['triage_seconds']}s\n")

    print("Hypothesis race (ranked by Granite risk):")
    for i, r in enumerate(c["all_ranked"], 1):
        mark = "  <-- winner" if (card.winner and r["id"] == card.winner.hypothesis.id) else ""
        print(f"  {i}. [{r['risk_score']:.2f}] {r['title']}{mark}")
        print(f"       {r['culprit_file']}:{r['culprit_symbol']} (line {r['line_hint']})")

    if c["critic"]:
        v = c["critic"]
        state = "REJECTED" if v["disproved"] else "CONFIRMED"
        print(f"\nAdversarial critic: {state}")
        print(f"  disproof test: {v['disproof_test']}")
        print(f"  reason: {v['verdict_reason']}")

    if c["suggested_fix"]:
        print(f"\nSuggested fix (byproduct): {c['suggested_fix']}")
    print("=" * 68 + "\n")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--trace", help="path to a trace/log file")
    g.add_argument("--text", help="inline trace text")
    args = ap.parse_args()

    trace = open(args.trace, encoding="utf-8").read() if args.trace else args.text
    card = asyncio.run(run_triage(trace))
    _print_card(card)
    from orchestrator.bob_shell import bobcoins_spent, calls_made
    print(f"Bobcoins this run: {bobcoins_spent():.4f} over {calls_made()} Bob calls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
