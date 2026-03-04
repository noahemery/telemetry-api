# Telemetry Data Processing API

A backend service to ingest, validate, clean, and analyze vehicle telemetry data — inspired by Formula Kentucky.

Built with **Python**, **FastAPI**, **SQLAlchemy**, **SQLite**, and **Jupyter**.

---

## Project Structure

```
telemetry-api/
├── app/
│   ├── main.py               # FastAPI app entry point
│   ├── db/
│   │   └── database.py       # SQLAlchemy engine & session
│   ├── models/
│   │   ├── session.py        # TestSession ORM model
│   │   └── telemetry.py      # TelemetryRecord ORM model
│   ├── schemas/
│   │   └── schemas.py        # Pydantic validation schemas
│   └── routers/
│       ├── sessions.py       # Session CRUD endpoints
│       └── telemetry.py      # Telemetry ingest + metrics endpoints
├── notebooks/
│   └── exploration.ipynb     # Jupyter prototyping & visualization
├── tests/
│   └── test_api.py           # Pytest test suite
├── requirements.txt
└── .gitignore
```

---

## Setup

### 1. Install Python
Download Python 3.11+ from https://python.org and make sure to check **"Add Python to PATH"** during install.

### 2. Clone / open in VS Code
```bash
git clone <your-repo-url>
cd telemetry-api
code .
```

### 3. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running the API

```bash
uvicorn app.main:app --reload
```

Then open your browser to:
- **Interactive docs (Swagger UI):** http://127.0.0.1:8000/docs
- **Alternative docs (ReDoc):** http://127.0.0.1:8000/redoc

---

## API Endpoints

### Sessions
| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions/` | Create a new test session |
| GET | `/sessions/` | List all sessions |
| GET | `/sessions/{id}` | Get a specific session |
| DELETE | `/sessions/{id}` | Delete a session |

### Telemetry
| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions/{id}/telemetry/` | Ingest a single record |
| POST | `/sessions/{id}/telemetry/bulk` | Ingest multiple records |
| GET | `/sessions/{id}/telemetry/` | Retrieve records (filter by lap) |
| GET | `/sessions/{id}/telemetry/metrics` | Get session-level metrics |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Jupyter Notebook

With the API running, launch Jupyter to explore and visualize data:

```bash
jupyter notebook notebooks/exploration.ipynb
```

The notebook lets you:
- Create sessions and ingest synthetic data
- Pull metrics
- Plot speed, RPM, and throttle/brake traces
- Compare laps side-by-side

---

## Validation Rules

The API enforces the following on every telemetry record:
- `speed_mph` must be ≥ 0
- `engine_rpm` must be between 0 – 20,000
- `throttle_pct` and `brake_pct` must be 0 – 100
- **Throttle and brake cannot both be > 0 at the same time**
- `gear` must be between 0 – 8

---

## Git Setup (first time)

```bash
git init
git add .
git commit -m "Initial commit: Telemetry API"
```

To push to GitHub, create a repo on github.com, then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/telemetry-api.git
git push -u origin main
```
