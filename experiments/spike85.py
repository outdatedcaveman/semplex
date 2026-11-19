"""Spike 85: whole-spectrum prediction of LM number geometry with the model's own action repertoire.
Value e_k: as Spike 82 (Fourier energy of the model's next-token predictive kernel over numbers 0..99).
Repertoire: the number transitions the model itself predicts after 'from {n} to' / '{n}, then' contexts: the set of
differences d = m - n (mod 100) carrying >= 5% of the pooled transition probability mass (repertoire, not usage:
each retained d weighted equally, per Spike 78). Cost c_k = mean over the repertoire of 1 - cos(2 pi k d / 100).
Predicted spectrum: P(k) ∝ e_k^alpha exp(-lambda c_k) (frozen Spike 77 parameters). Test: Spearman correlation of
the predicted spectrum with the learned Fourier spectrum of hidden states (Spike 82 hidden states, layer ~60%),
against energy-only and cost-only spectra. See SPIKE_85_REPORT.md."""
import json, os, sys
import numpy as np
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
import experiments.spike77 as S77
import experiments.spike82 as S82

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "results", "spike85.json")
PRED = os.path.join(ROOT, "results", "spike85_predictions.json")
TRANS = ["from{n} to", "{n}, then", "counting:{n},", "between{n} and", "after{n} comes"]
N = 100; ALPHA, LAMBDA = S77.ALPHA, S77.LAMBDA


def predict():
    P82 = json.load(open(S82.PRED)); P77 = json.load(open(S77.PRED)); res = {}
    for repo, pr in P82.items():
        if "skipped" in pr: continue
        tok, model = S82.load(repo)
        if tok.pad_token is None: tok.pad_token = tok.eos_token
        tok.padding_side = "right"
        ids = np.array([S82.numtok(tok, n)[0] for n in range(N)])
        mass = np.zeros(N)                                                     # pooled probability of each difference d
        for t in TRANS:
            Pn, _ = S82.forward(tok, model, [t.replace("{n}", " " + str(n)) for n in range(N)])
            Q = Pn[:, ids]                                                     # next-number distribution
            for n in range(N):
                for m_ in range(N): mass[(m_ - n) % N] += Q[n, m_]
        mass /= mass.sum()
        rep = [int(d) for d in np.where(mass >= 0.05)[0]]
        k = np.arange(1, N // 2 + 1)
        cost = np.array([np.mean([1 - np.cos(2 * np.pi * kk * d / N) for d in rep]) for kk in k]) if rep else np.zeros(len(k))
        e = np.array(pr["shares"])
        score = lambda a, lam: a * np.log(np.maximum(e, 1e-6)) - lam * cost
        sm = lambda s: np.exp(s - s.max()) / np.exp(s - s.max()).sum()
        res[repo] = {"repertoire": rep, "repertoire_mass": {str(d): float(mass[d]) for d in rep}, "cost": cost.tolist(),
                     "gibbs": sm(score(ALPHA, LAMBDA)).tolist(), "energy": sm(score(P77["energy_alpha"], 0.0)).tolist(),
                     "cost_only": sm(score(0.0, P77["smooth_lambda"])).tolist()}
        print(repo, "repertoire d:", rep, {d: round(mass[d], 3) for d in rep}, "top gibbs k:", (np.argsort(-np.array(res[repo]["gibbs"]))[:5] + 1).tolist(), flush=True)
        del model
    json.dump(res, open(PRED, "w"), indent=1)


def analyse():
    from scipy.stats import spearmanr
    P = json.load(open(PRED)); rows = {}; wins = []
    for repo, pr in P.items():
        H = np.load(os.path.join(S82.RAW, repo.replace("/", "__") + ".npz"))["H"].astype(np.float64)
        C = H - H.mean(0); C /= np.linalg.norm(C, axis=1, keepdims=True); G = C @ C.T; G = G - G.mean(0) - G.mean(1)[:, None] + G.mean()
        learned = S82.fourier_shares(G)
        rho = {m: float(spearmanr(np.log(np.array(pr[m]) + 1e-12), learned)[0]) for m in ("gibbs", "energy", "cost_only")}
        rows[repo] = {"rho": rho, "learned_top": (np.argsort(-learned)[:6] + 1).tolist(), "gibbs_top": (np.argsort(-np.array(pr["gibbs"]))[:6] + 1).tolist()}
        wins.append(rho["gibbs"] > max(rho["energy"], rho["cost_only"]))
    v = {"H85.1": "NO VERDICT" if len(wins) < 3 else ("HELD" if np.mean(wins) >= 2 / 3 else "BROKEN" if np.mean(wins) < 1 / 3 else "NEITHER"),
         "H85.2": "NO VERDICT" if len(rows) < 3 else ("HELD" if np.median([r["rho"]["gibbs"] for r in rows.values()]) >= 0.5 else "BROKEN" if np.median([r["rho"]["gibbs"] for r in rows.values()]) < 0.2 else "NEITHER")}
    out = {"verdicts": v, "models": rows}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"predict": predict, "analyse": analyse}[sys.argv[1]]()
