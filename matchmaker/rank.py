import os, time, hashlib
import pandas as pd
import numpy as np
from .nlp import normalize_text, embed
from .rules import rule_check
from .schemas import Patient

_CACHE = {
    "mtime": None, "df": None, "rows": 0, "updated": None,
    "embs": None, "texts": None, "npz": None, "live_hash": None
}

def _prep(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["EligibilityCriteria", "BriefTitle", "Condition", "LocationCountry"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    df["elig_norm"] = df["EligibilityCriteria"].map(normalize_text)
    df["title_norm"] = df["BriefTitle"].map(normalize_text)
    return df

def _hash_df(df: pd.DataFrame) -> str:
    key_cols = ["NCTId","BriefTitle","EligibilityCriteria"]
    sample = "|".join([f"{col}:{len(''.join(map(str, df[col].tolist()))) if col in df else 0}" for col in key_cols])
    return hashlib.md5(sample.encode("utf-8")).hexdigest()[:12]

def set_trials_df(df: pd.DataFrame, batch_size=256):
    df = _prep(df.copy())
    _CACHE["df"] = df
    _CACHE["rows"] = len(df)
    _CACHE["updated"] = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    _CACHE["mtime"] = None
    _CACHE["texts"] = (df["title_norm"] + " | " + df["elig_norm"]).tolist()

    live_hash = _hash_df(df)
    npz_path = f"data/trial_embs_{live_hash}.npz"
    _CACHE["npz"] = npz_path
    _CACHE["live_hash"] = live_hash

    if os.path.exists(npz_path):
        data = np.load(npz_path)
        _CACHE["embs"] = data["embs"]
        print(f"[set_trials_df] Loaded embeddings from {npz_path} ({_CACHE['embs'].shape[0]} trials)")
        return True

    texts = _CACHE["texts"]
    print(f"[set_trials_df] Building embeddings for {len(texts)} trials (batch={batch_size}) …")
    embs_list = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i:i+batch_size]
        embs_list.append(embed(chunk))
        print(f"  encoded {min(i+batch_size, len(texts))}/{len(texts)}")
    embs = np.vstack(embs_list).astype("float32")
    np.savez_compressed(npz_path, embs=embs)
    print(f"[set_trials_df] Saved embeddings -> {npz_path}")
    _CACHE["embs"] = embs
    return True

def rebuild_embeddings():
    npz_path = _CACHE.get("npz")
    if npz_path and os.path.exists(npz_path):
        try:
            os.remove(npz_path)
            print(f"[rebuild_embeddings] Deleted {npz_path}")
        except Exception as e:
            print(f"[rebuild_embeddings] Warning: {e}")
    _CACHE["embs"] = None
    if _CACHE.get("df") is not None:
        return set_trials_df(_CACHE["df"])
    raise RuntimeError("No trials loaded. Fetch live trials first.")

def last_cache_info():
    if _CACHE["rows"]:
        return {"rows": _CACHE["rows"], "updated": _CACHE["updated"]}
    return None

def cache_status():
    try:
        embs = _CACHE.get("embs")
        return {
            "trials_rows": int(_CACHE.get("rows") or 0),
            "trials_updated": _CACHE.get("updated"),
            "embeddings_memory": bool(embs is not None),
            "embeddings_vectors": int(embs.shape[0]) if embs is not None else 0,
            "embeddings_disk": bool(_CACHE.get("npz") and os.path.exists(_CACHE["npz"])),
        }
    except Exception as e:
        return {"error": str(e), "embeddings_memory": False, "embeddings_disk": False}

def _cosine(a, b):
    return np.matmul(a, b.T)

def _patient_query_text(p: Patient) -> str:
    bags = list(p.conditions) + list(p.medications)
    bags += [f"age {p.age}", p.sex]
    return " ; ".join([str(x).lower() for x in bags])

def rank_trials(patient: Patient, topk=50) -> list:
    df = _CACHE.get("df")
    if df is None or _CACHE.get("embs") is None:
        raise RuntimeError("Trials not loaded yet. Click 'Fetch live trials' first.")

    sub_df = df
    sub_embs = _CACHE["embs"]

    q = _patient_query_text(patient)
    q_emb = embed([q])
    sims = _cosine(q_emb, sub_embs).ravel()

    reasons = sub_df["elig_norm"].map(lambda t: rule_check(patient, t))
    scores = []
    for i, r in enumerate(reasons):
        penalty = -0.2 * len(r["exclude_reasons"])
        bonus   =  0.1 * len(r["include_reasons"])
        scores.append(float(sims[i]) + bonus + penalty)

    out = sub_df.copy()
    out["score"] = scores
    out["reasons_in"] = [r["include_reasons"] for r in reasons]
    out["reasons_out"] = [r["exclude_reasons"] for r in reasons]
    out = out.sort_values("score", ascending=False).head(topk)

    results = []
    for _, row in out.iterrows():
        nct = row["NCTId"]
        results.append({
            "nct_id": nct,
            "title": row["BriefTitle"],
            "condition": row["Condition"],
            "score": round(float(row["score"]), 3),
            "why_matched": row["reasons_in"],
            "why_excluded": row["reasons_out"],
            "nct_url": f"https://clinicaltrials.gov/ct2/show/{nct}",
            "status": row.get("OverallStatus","")
        })
    return results