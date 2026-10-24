# Ghost Data Still Exists — Audit API Backend

A read-only FastAPI service providing endpoints to explore deletion audit results, summary statistics, and evidence-backed case findings.

## Local Development

1. Navigate to the backend directory and install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

3. Open API docs in your browser:
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`
- Summary metrics: `http://localhost:8000/api/summary`
- Cases listing: `http://localhost:8000/api/cases`

## Render Deployment

This service can be deployed on [Render](https://render.com) using the included root `render.yaml` blueprint or as a Web Service:
- **Environment:** Python
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Root Directory:** `.` (so that `dataset/` and `output.csv` remain accessible)
