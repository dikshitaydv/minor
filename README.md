# Database Selection & Recommendation System

A student project that recommends a suitable database for an application using mandatory-requirement filtering, AHP criterion weights, TOPSIS ranking, and rule-based explanations.

## Initial database catalogue
PostgreSQL, MySQL, MongoDB, Cassandra, and Redis.

## Setup (Windows / VS Code)
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Current prototype status
- [x] Initial catalogue and application categories
- [x] Mandatory-requirement filtering
- [x] Basic rule-based explanations
- [ ] Integrate Jia's AHP weights module
- [ ] Integrate Jia's TOPSIS ranking module
- [ ] Save/load custom configurations and ranking history
- [ ] Expand evidence-backed catalogue and tests

## Important
Catalogue scores and application requirements in the initial prototype are demonstration values. Verify technical claims against official documentation before using results as research findings.
