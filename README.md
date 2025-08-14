# 🧬 Clinical Trial Matchmaker

Clinical Trial Matchmaker is an AI-powered web app that matches patients to relevant clinical trials from [ClinicalTrials.gov](https://clinicaltrials.gov).

Instead of relying on keyword search, it uses **semantic similarity** via [Sentence Transformers](https://www.sbert.net/) to find trials that are most relevant to a patient’s medical profile.

---

## 🚀 Features
- **Fetch live trial data** from ClinicalTrials.gov
- **Upload or use demo patients** for matching
- **AI embeddings** (`all-MiniLM-L6-v2`) for semantic search
- **Ranked matches** for each patient
- Filter trials by:
  - Recruitment status
  - Condition
  - Phase

---

## 🛠 How It Works
1. **Load patients** – Upload your own patient file or use the demo patients provided.
2. **Fetch trials** – Pull the latest trials from ClinicalTrials.gov.
3. **AI Matching** – The app embeds patient and trial descriptions into vectors and finds the most similar matches.
4. **View results** – See a ranked list of trials per patient with links to the trial details.

---

## 📦 Tech Stack
- **Backend**: Python, FastAPI / Gradio
- **AI Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Data Source**: ClinicalTrials.gov API
- **Deployment**: Hugging Face Spaces (Docker)

---

## 🌐 Live Demo

You can try the app directly here:
👉 [Hugging Face Space Link](https://huggingface.co/spaces/tambeneel/clinical-trial-matchmaker)

## 🙌 Acknowledgements
- Hugging Face for hosting
- Sentence Transformers for semantic embeddings
- ClinicalTrials.gov for providing trial data

---

