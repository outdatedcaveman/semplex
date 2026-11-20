"""Spike 82: the selection rule in pretrained language models. Concept: integers 0..99 as a cycle Z_100 under the
counting action +1. Value: Fourier energy (per frequency k = 1..50) of the model's OWN next-token predictive kernel
K(n,m) = mean over templates <p(.|ctx_n), p(.|ctx_m)> (centred). Cost: c_k = 1 - cos(2 pi k / 100) (kinetic cost of +1).
Frozen rule (alpha, lambda from Spike 77): P(k) ∝ e_k^alpha exp(-lambda c_k). Test: the leading Fourier mode of the
models' hidden-state geometry over numbers (residual at ~60% depth, at the number token, averaged over templates).
Two stages: `predict` reads only next-token distributions (outputs) and commits predictions; `run` then reads hidden
states. Telemetry off; models read from public weights. See SPIKE_82_REPORT.md."""
import json, os, sys
import numpy as np
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
import experiments.spike77 as S77

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike82_raw")
OUT = os.path.join(ROOT, "results", "spike82.json")
PRED = os.path.join(ROOT, "results", "spike82_predictions.json")
CACHE = os.path.expanduser("~/.cache/semplex-s68")
MODELS = ["openai-community/gpt2", "EleutherAI/pythia-410m", "HuggingFaceTB/SmolLM2-360M", "openai-community/gpt2-medium"]
TEMPLATES = ["I counted up to{n}", "There were{n}", "The answer is{n}", "She was born in the year 19{n2}", "Turn to page{n}",
             "The temperature was{n}", "He scored{n}", "It costs{n}", "We waited for{n}", "The total is{n}",
             "Chapter{n}", "Room number{n}", "Exactly{n}", "About{n}", "Only{n}", "At least{n}"]
N = 100; ALPHA, LAMBDA = S77.ALPHA, S77.LAMBDA


def numtok(tok, n):
    ids = tok.encode(" " + str(n), add_special_tokens=False)
    return ids if len(ids) == 1 else None


def contexts(tok):
    out = []
    for t in TEMPLATES:
        if "{n2}" in t:
            row = [t.replace("{n2}", f"{n:02d}") for n in range(N)]       # year: '19' + two digits as one token? checked below
        else:
            row = [t.replace("{n}", " " + str(n)) for n in range(N)]
        out.append(row)
    return out


def load(repo):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tok = AutoTokenizer.from_pretrained(repo, cache_dir=CACHE)
    model = AutoModelForCausalLM.from_pretrained(repo, cache_dir=CACHE, torch_dtype=torch.float32).eval()
    return tok, model


def forward(tok, model, texts, layer=None):
    """last-position next-token log-probs (top-2048 union later) and optionally the hidden state at the last position"""
    import torch
    P, Hs = [], []
    with torch.no_grad():
        for i in range(0, len(texts), 25):
            enc = tok(texts[i:i + 25], return_tensors="pt", padding=True)
            o = model(**enc, output_hidden_states=layer is not None)
            last = enc["attention_mask"].sum(1) - 1
            lg = o.logits[torch.arange(len(last)), last]
            P.append(torch.softmax(lg, -1).numpy().astype(np.float32))
            if layer is not None: Hs.append(o.hidden_states[layer][torch.arange(len(last)), last].numpy())
    return np.concatenate(P), (np.concatenate(Hs) if layer is not None else None)


def usable_templates(tok):
    keep = []
    for t in TEMPLATES:
        ok = all((numtok(tok, n) is not None) for n in range(N)) if "{n2}" not in t else False
        keep.append(ok)
    return [t for t, k in zip(TEMPLATES, keep) if k]


def fourier_shares(Kc):
    """isotypic energy share per frequency k = 1..50 of a (translation-averaged) kernel on Z_100"""
    n = len(Kc); w = np.zeros(n // 2 + 1)
    F = np.fft.fft2(Kc) / n
    for k in range(1, n // 2 + 1):
        w[k] = abs(F[k, k]) ** 2 + (abs(F[n - k, n - k]) ** 2 if k != n - k else 0)
    w = w[1:]; return w / w.sum()


def rule(shares, a=ALPHA, lam=LAMBDA):
    k = np.arange(1, len(shares) + 1); c = 1 - np.cos(2 * np.pi * k / N)
    s = a * np.log(np.maximum(shares, 1e-6)) - lam * c; p = np.exp(s - s.max()); return p / p.sum()


def predict():
    os.makedirs(RAW, exist_ok=True); P77 = json.load(open(S77.PRED)); res = {}
    for repo in MODELS:
        tok, model = load(repo)
        if tok.pad_token is None: tok.pad_token = tok.eos_token
        tok.padding_side = "right"
        temps = usable_templates(tok)
        if len(temps) < 6: res[repo] = {"skipped": f"only {len(temps)} templates with single-token numbers"}; print(repo, res[repo]); continue
        K = np.zeros((N, N))
        for t in temps:
            Pn, _ = forward(tok, model, [t.replace("{n}", " " + str(n)) for n in range(N)])
            Pn = np.sqrt(Pn)                                                   # Hellinger embedding of next-token distributions
            K += Pn @ Pn.T
        K /= len(temps); Kc = K - K.mean(0) - K.mean(1)[:, None] + K.mean()
        sh = fourier_shares(Kc); pg = rule(sh); pe = rule(sh, P77["energy_alpha"], 0.0); ps = rule(sh, 0.0, P77["smooth_lambda"])
        res[repo] = {"templates": temps, "shares": sh.tolist(), "gibbs": pg.tolist(), "energy": pe.tolist(), "smooth": ps.tolist(),
                     "argmax_k": {"gibbs": int(np.argmax(pg)) + 1, "energy": int(np.argmax(pe)) + 1, "smooth": int(np.argmax(ps)) + 1},
                     "layer": int(round(0.6 * model.config.num_hidden_layers))}
        top = np.argsort(-sh)[:6] + 1
        print(repo, "top energy k", top.tolist(), "pred", res[repo]["argmax_k"], flush=True)
        del model
    json.dump(res, open(PRED, "w"), indent=1)


def run():
    P = json.load(open(PRED)); os.makedirs(RAW, exist_ok=True)
    for repo, pr in P.items():
        if "skipped" in pr: continue
        pth = os.path.join(RAW, repo.replace("/", "__") + ".npz")
        if os.path.exists(pth): continue
        tok, model = load(repo)
        if tok.pad_token is None: tok.pad_token = tok.eos_token
        tok.padding_side = "right"
        Hsum = None
        for t in pr["templates"]:
            _, H = forward(tok, model, [t.replace("{n}", " " + str(n)) for n in range(N)], layer=pr["layer"])
            Hsum = H if Hsum is None else Hsum + H
        np.savez_compressed(pth, H=(Hsum / len(pr["templates"])).astype(np.float32)); print(repo, "hidden", Hsum.shape, flush=True)
        del model


def analyse():
    P = json.load(open(PRED)); rows = {}; nll = {"gibbs": 0.0, "energy": 0.0, "smooth": 0.0}; hits = []
    for repo, pr in P.items():
        if "skipped" in pr: continue
        H = np.load(os.path.join(RAW, repo.replace("/", "__") + ".npz"))["H"].astype(np.float64)
        C = H - H.mean(0); C /= np.linalg.norm(C, axis=1, keepdims=True); G = C @ C.T; G = G - G.mean(0) - G.mean(1)[:, None] + G.mean()
        sh = fourier_shares(G); lead = int(np.argmax(sh)) + 1
        for m in nll: nll[m] -= np.log(pr[m][lead - 1] + 1e-12)
        hits.append(lead == pr["argmax_k"]["gibbs"])
        rows[repo] = {"lead_k": lead, "top_learned_k": (np.argsort(-sh)[:6] + 1).tolist(), "learned_shares_top": sorted(sh.tolist(), reverse=True)[:6], "pred": pr["argmax_k"]}
    n = len(hits); v = {}
    v["H82.1"] = "NO VERDICT" if n < 3 else ("HELD" if np.mean(hits) >= 2 / 3 and nll["gibbs"] < min(nll["energy"], nll["smooth"]) else "BROKEN" if np.mean(hits) < 1 / 3 else "NEITHER")
    out = {"verdicts": v, "acc": float(np.mean(hits)) if hits else None, "nll": nll, "models": rows}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"predict": predict, "run": run, "analyse": analyse}[sys.argv[1]]()
