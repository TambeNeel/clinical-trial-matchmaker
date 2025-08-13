# Clinical Trial Matchmaker (Flask, Live API)

End-to-end demo that matches synthetic patients to **live** recruiting trials from ClinicalTrials.gov (v2 API).  
Not medical advice. No PHI.

## Run locally
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:7860

Click **Fetch live trials** first (Quick/Medium/Full). Then choose a demo patient and **Find Trials**.

## Deploy (Render / Railway / Heroku)
- Build: pip install -r requirements.txt
- Start: gunicorn app:app --preload --timeout 180 -b 0.0.0.0:$PORT

## Deploy with Docker
docker build -t ct-matchmaker .
docker run -p 7860:7860 ct-matchmaker

## API
- POST /api/match → JSON {patient schema} → ranked trials
- GET /healthz → JSON status

Notes:
- Embeddings are cached to data/trial_embs_*.npz, keyed by the dataset hash.
- Patients in data/patients/ are synthetic. Educational use only.