# ShadowLink — Threat Actor De-anonymization Platform (SIH 26151)

> **⚠️ DEMO MODE — SYNTHETIC DATA ONLY**
> This repository contains a fully self-contained offline demonstration built for Smart India Hackathon 26151. It does NOT connect to the dark web, scrape real onion services, or process real personally identifiable information (PII). All cryptographic keys, infrastructure IPs, and stylized text posts are artificially generated using a reproducible seed (`26151`).

## 🧱 Architecture Overview

ShadowLink correlates three previously isolated intelligence streams to unmask threat actors:
1. **Infrastructure Intelligence:** Matches TLS/SSL certificates and custom HTTP server banners between `.onion` darknet services and clearnet IPs.
2. **Cryptographic Intelligence:** Correlates leaked PGP public keys and cryptocurrency wallet addresses across multiple aliases and forums.
3. **Stylometric Intelligence:** Uses NLP (TF-IDF + Cosine Similarity) to identify distinct grammatical and stylistic fingerprints, linking "rebranded" personas that share zero cryptographic or infrastructure overlap.

The system uses a **FastAPI** backend with a **NetworkX** graph engine, exposing REST endpoints to a vanilla **HTML5/Tailwind/Cytoscape.js** frontend dashboard.

---

## 🚀 How to Run the Demo

### 1. Start the Backend API
The backend handles the data generation, SQLite in-memory database provisioning, and module execution automatically on startup.

1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Activate the virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```
3. Start the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   *You should see output indicating the seed data was loaded and modules ran successfully.*

### 2. Launch the Frontend Dashboard
The frontend requires **zero build steps** (no Node.js/npm required).
1. Open a new file explorer window and navigate to the `frontend` directory.
2. Double-click **`index.html`** to open it in your browser (Chrome/Edge/Firefox).

---

## 🎯 Navigating the Dashboard

- **Dashboard (Command Center):** View top-level metrics and a prioritized list of threat actors.
- **Identity Graph:** An interactive, force-directed graph (Cytoscape.js) showing the connections between actor personas.
  - 🟢 Green lines: `SAME_PGP`
  - 🟠 Orange lines: `SAME_WALLET`
  - 🟣 Dashed Purple lines: `STYLE_MATCH` (Stylometry)
  - 🔵 Blue lines: `VOUCHED_FOR`
- **Infra Leaks:** View the direct TLS/SSL correlations unmasking onion services to clearnet IPs.
- **Stylometry:** Review AI-suggested linguistic matches. You can click "VERIFY MATCH" to simulate a human-in-the-loop analyst promoting an AI suggestion to a confirmed link.
- **PDF Dossier Export:** From the dashboard table or any actor detail modal, click the **PDF / Export** button to generate a court-ready HTML intelligence dossier.

---

## 🧩 Modifying the Seed Data (For Developers)

To change the synthetic data generation parameters or see how the metrics perform with different volumes:
1. Stop the backend server (`Ctrl+C`).
2. Delete the `backend/shadowlink.db` SQLite file.
3. Edit `backend/app/seed/generate_seed.py` (e.g., change `NUM_ACTORS`).
4. Run `python app/seed/generate_seed.py` to rebuild the JSON dataset.
5. Restart the backend server.
