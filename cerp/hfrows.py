"""Read selected rows of an open model's embedding matrices straight from its
published safetensors file, with HTTP range requests (no full download, no
model run). Downloaded bytes are treated as data: only the JSON header and raw
tensor bytes are parsed; nothing is executed."""
import json, os, struct, urllib.request
import numpy as np

HF = "https://huggingface.co"
UA = {"User-Agent": "semplex-hfrows/0.1"}
CACHE = os.environ.get("SEMPLEX_HF_CACHE", os.path.expanduser("~/.cache/semplex-hf"))
DT = {"F32": (np.float32, 4), "F16": (np.float16, 2), "BF16": (None, 2)}


def _get(url, rng=None):
    h = dict(UA)
    if rng:
        h["Range"] = "bytes=%d-%d" % rng
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as r:
        return r.read()


def _file(repo, name):
    p = os.path.join(CACHE, repo.replace("/", "__"), name)
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        d = _get(f"{HF}/{repo}/resolve/main/{name}")
        open(p, "wb").write(d)
    return p


def tokenizer(repo):
    from tokenizers import Tokenizer
    return Tokenizer.from_file(_file(repo, "tokenizer.json"))


def _headers(repo):
    """{tensor name: (file, dtype, shape, absolute byte offset)}"""
    p = os.path.join(CACHE, repo.replace("/", "__"), "headers.json")
    if os.path.exists(p):
        return json.load(open(p))
    try:
        idx = json.load(open(_file(repo, "model.safetensors.index.json")))
        files = sorted(set(idx["weight_map"].values()))
    except Exception:
        files = ["model.safetensors"]
    out = {}
    for f in files:
        url = f"{HF}/{repo}/resolve/main/{f}"
        n = struct.unpack("<Q", _get(url, (0, 7)))[0]
        hd = json.loads(_get(url, (8, 8 + n - 1)))
        for k, v in hd.items():
            if k == "__metadata__":
                continue
            out[k] = (f, v["dtype"], v["shape"], 8 + n + v["data_offsets"][0])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w"))
    return out


EMB = ("wte.weight", "embed_tokens.weight", "embed_in.weight", "word_embeddings.weight", "tok_embeddings.weight", "embed.weight", "wte")
UNEMB = ("lm_head.weight", "embed_out.weight", "output.weight")


def matrices(repo):
    """names of the input-embedding and (if untied) unembedding tensors"""
    h = _headers(repo)
    pick = lambda pats: next((k for k in sorted(h, key=len) if any(k.endswith(p) for p in pats) and len(h[k][2]) == 2), None)
    return pick(EMB), pick(UNEMB), h


def rows(repo, tensor, ids):
    h = _headers(repo)
    f, dt, shape, off = h[tensor]
    np_dt, sz = DT[dt]
    d = shape[1]
    url = f"{HF}/{repo}/resolve/main/{f}"
    out = []
    for i in ids:
        cp = os.path.join(CACHE, repo.replace("/", "__"), "rows", f"{tensor}.{i}.npy")
        if os.path.exists(cp):
            out.append(np.load(cp)); continue
        b = _get(url, (off + i * d * sz, off + (i + 1) * d * sz - 1))
        if dt == "BF16":
            v = (np.frombuffer(b, np.uint16).astype(np.uint32) << 16).view(np.float32)
        else:
            v = np.frombuffer(b, np_dt).astype(np.float32)
        os.makedirs(os.path.dirname(cp), exist_ok=True)
        np.save(cp, v)
        out.append(v)
    return np.stack(out)
