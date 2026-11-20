"""Angelic proof checking for Lean 4, after MathEye (Chen et al., arXiv 2611.22103), reimplemented here because no code
was released. Usage:

    python -m cerp.angelic FILE.lean [--project DIR] [--out REPORT.json]

1. Angelic check: compile; replace each failing tactic step with `sorry` (marked `-- ANGELIC[k]: <original>`), and
   close each "unsolved goals" block with `sorry`, until the file checks with sorries only. The proof outline survives.
2. Goal extraction: the goal state at every obligation (via `trace_state`).
3. Residual analysis: try automation on each obligation with every other obligation still assumed. Obligations are in
   source order, so a goal can only use hypotheses introduced before it; closing all individually closable obligations
   at once is therefore sound (no circular reliance). What remains is the ESSENTIAL set: the questions for a human.
   (MathEye solves a MaxSAT over a symbol-level dependence graph; this greedy residual is the simple, sound special case.)
4. Report: obligations, goals, which automation closed which, and the essential set, with the dependence edges
   (which essential obligations introduce hypotheses that later obligations use).
The patched file (`FILE.angelic.lean`) keeps the outline; answers from the human are then written into it and the tool
is re-run until there is no `sorry` left. Final audit: `#print axioms` must not list `sorryAx`.
"""
import json, os, re, subprocess, sys

AUTO_CORE = ["decide", "rfl", "simp", "omega", "simp_all", "constructor <;> simp_all"]
AUTO_MATHLIB = ["norm_num", "ring", "linarith", "nlinarith", "positivity", "aesop", "field_simp", "simp_all", "exact?"]


def lean_cmd(project):
    elan = os.path.expanduser("~/.elan/bin")
    env = dict(os.environ, PATH=elan + os.pathsep + os.environ.get("PATH", ""))
    if project and os.path.exists(os.path.join(project, "lakefile.lean")) or project and os.path.exists(os.path.join(project, "lakefile.toml")):
        return ["lake", "env", "lean", "--json"], env
    return ["lean", "--json"], env


def check(src, path, project, timeout=1200):
    """compile `src` written at `path`; return list of messages (dicts with severity, line, col, endLine, text)"""
    open(path, "w").write(src)
    cmd, env = lean_cmd(project)
    p = subprocess.run(cmd + [os.path.abspath(path)], cwd=project or os.path.dirname(os.path.abspath(path)),
                       capture_output=True, text=True, timeout=timeout, env=env)
    msgs = []
    for line in p.stdout.splitlines():
        try: m = json.loads(line)
        except json.JSONDecodeError: continue
        msgs.append({"severity": m.get("severity"), "line": m["pos"]["line"], "col": m["pos"]["column"],
                     "endLine": (m.get("endPos") or m["pos"])["line"], "text": m.get("data", "")})
    if not msgs and p.returncode != 0:
        msgs.append({"severity": "error", "line": 1, "col": 0, "endLine": 1, "text": (p.stderr or p.stdout)[:2000]})
    return msgs


def indent(s): return len(s) - len(s.lstrip(" "))


def block_end(lines, i):
    """last line index of the tactic step starting at i (following lines indented deeper)"""
    k, j = indent(lines[i]), i + 1
    while j < len(lines) and (lines[j].strip() == "" or indent(lines[j]) > k):
        j += 1
    while j - 1 > i and lines[j - 1].strip() == "": j -= 1
    return j - 1


def rest_of_block(lines, i):
    """a failing step and every later step of the same tactic block: once the step is `sorry` the goal is closed, so
    the remaining steps are dead. A focus bullet (`·`) covers only its own body; sibling bullets are kept."""
    k = indent(lines[i]); bullet = lines[i].lstrip().startswith("·"); j = i + 1
    while j < len(lines):
        L = lines[j]
        if L.strip() == "" or indent(L) > k or (not bullet and indent(L) == k and not L.lstrip().startswith(("·", "|"))
                                                  and not re.match(r"\s*(theorem|lemma|def|end|namespace|/--|@\[)", L)):
            j += 1
        else: break
    while j - 1 > i and lines[j - 1].strip() == "": j -= 1
    return j - 1


def tactic_line(lines, i):
    """the tactic step containing line i: walk back over blank lines and deeper-indented continuation lines"""
    while i > 0 and lines[i].strip() == "": i -= 1
    return i


def angelic(src, path, project, max_iter=60):
    lines = src.split("\n"); k = 0; log = []
    for _ in range(max_iter):
        msgs = check("\n".join(lines), path, project); errs = [m for m in msgs if m["severity"] == "error"]
        if not errs: return "\n".join(lines), k, log, msgs
        e = errs[0]; i = e["line"] - 1
        if "ANGELIC" in lines[min(i, len(lines) - 1)] and not e["text"].startswith("unsolved goals"):
            raise RuntimeError(f"an angelic edit broke the file at line {e['line']}: {e['text'][:200]}")
        if e["text"].startswith("unsolved goals"):
            # the block that failed to close: append `sorry` after its last line, at the block's tactic indentation
            j = min(e["endLine"] - 1, len(lines) - 1)
            start = i if lines[i].rstrip().endswith("by") else i
            body = [x for x in range(start + 1, j + 1) if lines[x].strip()]
            ind = indent(lines[body[0]]) if body else indent(lines[start]) + 2
            lines.insert(j + 1, " " * ind + f"sorry -- ANGELIC[{k}]: unsolved goals")
        else:
            i = tactic_line(lines, i); j = rest_of_block(lines, i); orig = lines[i].strip()
            m = re.match(r"(\s*)(have|obtain|show|suffices)\b(.*?):=\s*by\b.*", lines[i])
            if m and j > i:                                              # keep the `have` statement, drop its proof
                lines[i:j + 1] = [lines[i][:lines[i].index(":= by")] + f":= by sorry -- ANGELIC[{k}]: {orig[:80]}"]
            else:
                mh = re.match(r"(\s*)(have|obtain)\b(.*?):=(.*)", lines[i])
                if mh:
                    lines[i:j + 1] = [lines[i][:lines[i].index(":=")] + f":= by sorry -- ANGELIC[{k}]: {orig[:80]}"]
                else:
                    L = lines[i]; st = indent(L); code = L.split("--")[0]
                    arrow = code.rfind("=>", 0, max(e["col"], 0) + 1) if lines[i] == lines[e["line"] - 1] else -1
                    if arrow >= 0: st = arrow + 2                                  # `| case => tactic`: keep the arm
                    elif code.lstrip().startswith("·"): st = code.index("·") + 1    # focus dot
                    lines[i:j + 1] = [L[:st].rstrip() + " " * (1 if st > indent(L) else 0) + f"sorry -- ANGELIC[{k}]: {orig[:80]}" if st > indent(L)
                                      else " " * st + f"sorry -- ANGELIC[{k}]: {orig[:80]}"]
        log.append({"k": k, "line": e["line"], "error": e["text"][:300]}); k += 1
    raise RuntimeError("angelic check did not converge; see log:\n" + json.dumps(log[-3:], indent=1))


def obligations(src):
    """every `sorry` in the file (angelic or authored) is an obligation"""
    out = []
    for i, l in enumerate(src.split("\n")):
        for m in re.finditer(r"\bsorry\b", l.split("--")[0]):
            out.append({"line": i + 1, "col": m.start(), "tag": (re.search(r"ANGELIC\[(\d+)\]: (.*)", l) or [None, None, None])[2] if "ANGELIC" in l else "authored"})
    return out


def replace_nth_sorry(src, ob, repl):
    lines = src.split("\n"); l = lines[ob["line"] - 1]
    lines[ob["line"] - 1] = l[:ob["col"]] + repl + l[ob["col"] + len("sorry"):]
    return "\n".join(lines)


def goals(src, path, project, obs):
    """goal state at each obligation (trace_state before the sorry)"""
    res = []
    for ob in obs:
        s = replace_nth_sorry(src, ob, "(trace_state; sorry)")
        msgs = check(s, path, project)
        g = [m["text"] for m in msgs if m["severity"] == "information" and m["line"] == ob["line"]]
        res.append(g[0] if g else "(goal not captured)")
    return res


def residual(src, path, project, obs, tactics):
    closed = {}
    for n, ob in enumerate(obs):
        for t in tactics:
            s = replace_nth_sorry(src, ob, f"({t})")
            msgs = check(s, path, project)
            if not any(m["severity"] == "error" for m in msgs):
                closed[n] = t; break
    return closed


def deps(goal_texts, obs, src):
    """edge i -> j when the hypothesis that obligation i proves (its enclosing `have`) is in obligation j's goal context,
    i.e. j may rely on i. These are availability edges, not proven uses."""
    names = {}
    for n, ob in enumerate(obs):
        L = src.split("\n"); i = ob["line"] - 1; k = indent(L[i]) + 1
        while i >= 0:                                            # this line, or the enclosing (shallower) `have`
            if L[i].strip() and indent(L[i]) < k:
                m = re.match(r"\s*(?:have|obtain)\s+([A-Za-z_][\w']*)", L[i])
                if m: names[n] = m.group(1); break
                k = indent(L[i])
                if k == 0: break
            i -= 1
    E = []
    for i, h in names.items():
        for j, g in enumerate(goal_texts):
            if j > i and re.search(rf"(^|\n)\s*{re.escape(h)}\s*:", g): E.append([i, j])
    return E


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--project"); ap.add_argument("--out")
    ap.add_argument("--mathlib", action="store_true", help="also try Mathlib automation (norm_num, linarith, aesop, exact? ...)")
    a = ap.parse_args(argv)
    src = open(a.file).read(); work = a.file.replace(".lean", ".angelic.lean")
    patched, n_new, log, _ = angelic(src, work, a.project)
    obs = obligations(patched); G = goals(patched, work, a.project, obs)
    tac = AUTO_CORE + (AUTO_MATHLIB if a.mathlib else [])
    closed = residual(patched, work, a.project, obs, tac)
    final = patched
    for n in sorted(closed, key=lambda n: (-obs[n]["line"], -obs[n]["col"])):     # bottom-up keeps positions valid
        final = replace_nth_sorry(final, obs[n], f"({closed[n]})")
    ok = not any(m["severity"] == "error" for m in check(final, work, a.project))
    if not ok: final = patched; closed = {}                                    # joint check failed: keep all as essential
    open(work, "w").write(final)
    ess = [n for n in range(len(obs)) if n not in closed]
    rep = {"file": a.file, "patched": work, "new_angelic_sorries": n_new, "angelic_log": log,
           "obligations": [{**ob, "id": n, "goal": G[n], "closed_by": closed.get(n), "essential": n in ess} for n, ob in enumerate(obs)],
           "essential": ess, "context_edges": deps(G, obs, patched), "joint_check_ok": ok}
    out = a.out or a.file.replace(".lean", ".angelic.json"); json.dump(rep, open(out, "w"), indent=1)
    print(f"{len(obs)} obligations ({n_new} from failing steps); {len(closed)} closed by automation; {len(ess)} essential -> {out}")
    for n in ess: print(f"\n[{n}] line {obs[n]['line']} ({obs[n]['tag']})\n{G[n]}")


if __name__ == "__main__":
    main(sys.argv[1:])
