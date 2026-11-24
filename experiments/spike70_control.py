"""Spike 70, exploratory control after the verdicts (H70.3's R^2>=0.9 swap criterion is uninformative at
sigma 0.15: the 20-step output window has little variance, so a 0.1 rad donor mismatch fails it).
Retrains seeds 0-1 of each readout (same seeds, same code path) and compares output MSE (vs the no-swap truth)
after an ANTIPODAL swap against a SAME-STATE swap (donor within 0.1 rad of u). Ratio ~1: the sign is causally
inert for the outputs; ratio >> 1: causal. Also: the registered sign probe (H70.2) was not class-balanced
(only ~4% of states with |u_z|>=0.3 have u_z<0, so chance is ~0.96); this reports balanced accuracy."""
import json, os
import numpy as np
import torch
import experiments.spike70 as S

def main():
    torch.set_num_threads(2); res = []
    for ro in S.READOUTS:
        for i in range(2):
            seed = 7000 + 10 * S.READOUTS.index(ro) + i
            torch.manual_seed(seed); rng = np.random.default_rng(seed); k_out = 3 if ro == "SIGN" else 5
            gru = torch.nn.GRU(3, 64, batch_first=True); head = torch.nn.Linear(64, k_out)
            opt = torch.optim.Adam(list(gru.parameters()) + list(head.parameters()), lr=0.003)
            sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, S.STEPS)
            for step in range(S.STEPS):
                W, Y, _ = S.sample(ro, 64, S.LEN, rng)
                loss = ((head(gru(torch.tensor(W))[0]) - torch.tensor(Y)) ** 2).mean()
                opt.zero_grad(); loss.backward(); opt.step(); sch.step()
            with torch.no_grad():
                W, Y, U = S.sample(ro, 500, S.MLEN, np.random.default_rng(seed + 2 * 10**6)); H = gru(torch.tensor(W))[0].numpy()
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import balanced_accuracy_score
            Hs, Us = H[:, 5:].reshape(-1, 64), U[:, 5:].reshape(-1, 3); m = np.abs(Us[:, 2]) >= 0.3
            Xs, ys = Hs[m], (Us[m, 2] > 0).astype(int); hl = len(ys) // 2
            clf = LogisticRegression(max_iter=3000, class_weight="balanced").fit(Xs[:hl], ys[:hl])
            bal = float(balanced_accuracy_score(ys[hl:], clf.predict(Xs[hl:]))); minority = float(min(ys.mean(), 1 - ys.mean()))
            fU = U[:, 5:].reshape(-1, 3); fH = H[:, 5:].reshape(-1, 64); ir = np.random.default_rng(seed + 5 * 10**6)
            ea, es = [], []
            for _ in range(1500):
                b = int(ir.integers(500)); t = int(ir.integers(5, S.MLEN - 21)); u = U[b, t]
                ja = int(np.argmax(fU @ (-u))); js = np.argsort(-(fU @ u))
                js = [j for j in js[:50] if not np.allclose(fH[j], H[b, t])]
                if np.arccos(np.clip(fU[ja] @ (-u), -1, 1)) > 0.1 or not js or np.arccos(np.clip(fU[js[0]] @ u, -1, 1)) > 0.1: continue
                truth = Y[b, t + 1:t + 21]; suf = torch.tensor(W[b, t + 1:t + 21][None])
                with torch.no_grad():
                    oa = head(gru(suf, torch.tensor(fH[ja][None, None]))[0]).numpy()[0]
                    os_ = head(gru(suf, torch.tensor(fH[js[0]][None, None]))[0]).numpy()[0]
                ea.append(((oa - truth) ** 2).mean()); es.append(((os_ - truth) ** 2).mean())
            r = {"readout": ro, "seed": seed, "n": len(ea), "mse_antipodal_swap": float(np.mean(ea)), "mse_same_state_swap": float(np.mean(es)),
                 "ratio": float(np.mean(ea) / np.mean(es)),
                 "sign_probe_balanced_accuracy": bal, "sign_minority_fraction": minority}
            print(r, flush=True); res.append(r)
    json.dump(res, open(os.path.join(S.ROOT, "results", "spike70_control.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
