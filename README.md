# AI Customer Support Analytics Platform — Dashboard Prototype

A working Streamlit dashboard built from the PRD, wired up to **synthetic ticket
data** so every chart, KPI, and table is live rather than a static mockup.
This covers step 8 of the PRD (UI/Dashboard) plus working versions of Ticket
Management, Analytics, Team Performance, and CSV export.

## What's real vs. what's a stub

| Piece | Status |
|---|---|
| Dashboard Overview (KPIs, satisfaction trend, sentiment donut, top issues, team performance) | **Fully functional**, reads from SQLite |
| Tickets page (search + filter by sentiment/topic/status) | **Fully functional** |
| Analytics page (topic volume over time, confidence by sentiment, resolution status) | **Fully functional** |
| Team Performance page | **Fully functional** |
| Reports → CSV export | **Fully functional** |
| Reports → PDF export | Stub — noted in-app, not wired up yet |
| Settings page | UI only — not persisted |
| Sentiment/topic labels | **Synthetic** — generated with realistic weighting, not predicted by a real ML model yet |

The next phase (per the PRD) is the FastAPI backend + the actual sentiment/topic
ML model, which would replace `data_generator.py` as the source of truth and
give this dashboard a real ticket-submission pipeline to read from.

## Project structure

```
support-analytics-dashboard/
├── app.py              # Streamlit app: layout, pages, navigation
├── charts.py           # Plotly chart builders (colors, styling)
├── database.py         # SQLite query layer (KPIs, trends, aggregates)
├── data_generator.py   # Synthetic ticket generator (1,248 tickets, 60 days)
├── requirements.txt
└── data/
    └── tickets.db       # created automatically on first run
```

## Setup

Requires Python 3.10+.

```bash
cd support-analytics-dashboard
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

This opens the dashboard at `http://localhost:8501`. The SQLite database is
generated automatically the first time you run it (1,248 synthetic tickets
spread across the last 60 days, weighted ~51% positive / 25% neutral / 17%
negative / 6% urgent-negative, matching the PRD's sample numbers).

To regenerate the data with a different volume, edit the call in
`data_generator.py`'s `__main__` block or run:

```bash
python -c "from data_generator import build_database; build_database(force=True)"
```

## Notes for the next build phase

- `database.py` is the seam where the real backend plugs in — swap the SQLite
  queries for calls to the FastAPI service once it exists, and the dashboard
  pages don't need to change.
- The synthetic sentiment/topic labels in `data_generator.py` were generated
  with fixed weights so charts look like the PRD mock. Once the real ML model
  (scikit-learn / Hugging Face Transformers, per the PRD tech stack) is
  producing labels, those weights become actual predictions instead.
