"""Fixed run command for OpenResearch (and for anyone): one command, every experiment node.

    python -m experiments.orx_run

OpenResearch's run contract: every node of the experiment tree runs the *same* command,
with no environment variables. Only the committed code differs between nodes. So
what a node runs is itself committed: `experiments/orx_node.json` on the node's
branch names the spike and the steps it executes. To make a new node, branch it,
edit that file (and the spike's code), commit, and run the same command.

The log prints (1) the effective configuration, (2) every step's output, and
(3) a compact final summary of the spike's result file, as the orx-results
module requires.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
NODE = ROOT / "experiments" / "orx_node.json"


def compact(x, depth=0):
    if isinstance(x, float):
        return round(x, 4)
    if isinstance(x, dict):
        return {k: compact(v, depth + 1) for k, v in list(x.items())[:40]} if depth < 4 else "…"
    if isinstance(x, list):
        return [compact(v, depth + 1) for v in x[:12]] + (["…"] if len(x) > 12 else [])
    return x


def main():
    node = json.loads(NODE.read_text())
    git = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    print("== effective configuration ==", json.dumps({**node, "commit": git, "python": sys.version.split()[0]}, indent=1), sep="\n", flush=True)
    report = ROOT / node["report"]
    text = report.read_text() if report.exists() else ""
    if "pre-registered (no run made)" not in text and "complete" not in text:
        sys.exit(f"refusing to run: {node['report']} has no pre-registration status line")
    for step in node["steps"]:
        cmd = [sys.executable, "-m", f"experiments.{node['module']}", *step]
        t0 = time.time()
        print(f"== step: {' '.join(step)} ==", flush=True)
        r = subprocess.run(cmd, cwd=ROOT)
        print(f"== step done: {' '.join(step)} exit={r.returncode} seconds={time.time() - t0:.0f} ==", flush=True)
        if r.returncode:
            sys.exit(r.returncode)
    out = ROOT / node["result"]
    print("== final summary ==", flush=True)
    print(json.dumps(compact(json.loads(out.read_text())), indent=1) if out.exists() else f"no result file at {node['result']}")


if __name__ == "__main__":
    main()
