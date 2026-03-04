from fastapi import FastAPI
from app.db.database import init_db
from app.routers import sessions, telemetry

app = FastAPI(
    title="Telemetry Data Processing API",
    description="Ingest, validate, and analyze vehicle telemetry data from test sessions.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(sessions.router)
app.include_router(telemetry.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Telemetry API is running."}
