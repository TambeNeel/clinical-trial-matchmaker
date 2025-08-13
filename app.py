import os, glob, io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from matchmaker.rank import rank_trials, cache_status, rebuild_embeddings, set_trials_df, last_cache_info
from matchmaker.schemas import Patient, load_patient
from matchmaker import etl

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

def list_patient_ids():
    import os
    files = sorted(glob.glob("data/patients/*.json"))
    return [os.path.splitext(os.path.basename(f))[0] for f in files]

@app.route("/", methods=["GET", "POST"])
def index():
    demo_ids = list_patient_ids()
    if not demo_ids:
        return "No demo patients found in data/patients", 500
    preset = request.args.get("preset", "quick")
    selected_id = request.form.get("patient", demo_ids[0])
    results = None
    if request.method == "POST" and request.form.get("action") == "match":
        patient = load_patient(selected_id)
        results = rank_trials(patient)
    cache_meta = last_cache_info()
    status = cache_status()
    status_ok = (not status.get("error")) and (status.get("trials_rows", 0) > 0) and bool(status.get("embeddings_memory"))
    return render_template("index.html", patients=demo_ids, selected_id=selected_id, results=results,
                           cache_meta=cache_meta, status=status, status_ok=status_ok, preset=preset)

@app.route("/refresh", methods=["POST"])
def refresh():
    preset = request.args.get("preset", "quick")
    presets = {
        "quick": dict(cond_query='("type 2 diabetes" OR diabetes OR "heart failure" OR cancer)', statuses=("RECRUITING",), page_size=200, max_pages=3),
        "medium": dict(cond_query='(diabetes OR "heart failure" OR cancer OR stroke OR asthma)', statuses=("RECRUITING",), page_size=200, max_pages=8),
        "full": dict(cond_query='(diabetes OR "heart failure" OR cancer OR stroke OR asthma OR COPD OR "chronic kidney disease")', statuses=("RECRUITING",), page_size=200, max_pages=20),
    }
    cfg = presets.get(preset, presets["quick"])
    try:
        df = etl.fetch_trials_v2(**cfg)
        set_trials_df(df)
        flash(f"Fetched {len(df)} live trials and updated embeddings ({preset}).", "success")
    except Exception as e:
        flash(f"Refresh failed: {e}", "danger")
    return redirect(url_for("index", preset=preset))

@app.route("/rebuild_embeddings", methods=["POST"])
def rebuild():
    try:
        rebuild_embeddings()
        flash("Embeddings rebuilt and cached.", "success")
    except Exception as e:
        flash(f"Rebuild failed: {e}", "danger")
    return redirect(url_for("index", preset=request.args.get("preset", "quick")))

@app.route("/export", methods=["POST"])
def export_csv():
    preset = request.args.get("preset", "quick")
    selected_id = request.form.get("patient")
    if not selected_id:
        flash("No patient selected for export.", "danger")
        return redirect(url_for("index", preset=preset))
    patient = load_patient(selected_id)
    results = rank_trials(patient)
    df = pd.DataFrame(results)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    mem = io.BytesIO(csv_bytes)
    filename = f"trial_matches_{selected_id}.csv"
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=filename)

@app.route("/healthz", methods=["GET"])
def healthz():
    s = cache_status()
    ok = not s.get("error") and s.get("trials_rows", 0) > 0 and bool(s.get("embeddings_memory"))
    return jsonify({"ok": ok, **s})

@app.route("/api/match", methods=["POST"])
def api_match():
    data = request.get_json(force=True)
    p = Patient(**data)
    results = rank_trials(p)
    return jsonify({"count": len(results), "results": results})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    app.run(host="0.0.0.0", port=port)