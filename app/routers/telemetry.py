from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.db.database import get_db
from app.models.session import TestSession
from app.models.telemetry import TelemetryRecord
from app.schemas.schemas import TelemetryRecordCreate, TelemetryRecordResponse, SessionMetrics

router = APIRouter(prefix="/sessions/{session_id}/telemetry", tags=["Telemetry"])


def _get_session_or_404(session_id: int, db: Session) -> TestSession:
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.post("/", response_model=TelemetryRecordResponse, status_code=201)
def ingest_record(session_id: int, payload: TelemetryRecordCreate, db: Session = Depends(get_db)):
    _get_session_or_404(session_id, db)
    record = TelemetryRecord(session_id=session_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/bulk", response_model=dict, status_code=201)
def ingest_bulk(session_id: int, records: List[TelemetryRecordCreate], db: Session = Depends(get_db)):
    _get_session_or_404(session_id, db)
    db_records = [TelemetryRecord(session_id=session_id, **r.model_dump()) for r in records]
    db.bulk_save_objects(db_records)
    db.commit()
    return {"inserted": len(db_records)}


@router.get("/", response_model=List[TelemetryRecordResponse])
def get_records(
    session_id: int,
    lap: int | None = None,
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    _get_session_or_404(session_id, db)
    query = db.query(TelemetryRecord).filter(TelemetryRecord.session_id == session_id)
    if lap is not None:
        query = query.filter(TelemetryRecord.lap_number == lap)
    return query.order_by(TelemetryRecord.xtime).offset(skip).limit(limit).all()


@router.get("/metrics", response_model=SessionMetrics)
def get_session_metrics(session_id: int, db: Session = Depends(get_db)):
    session = _get_session_or_404(session_id, db)

    agg = db.query(
        func.count(TelemetryRecord.id),
        func.min(TelemetryRecord.xtime),
        func.max(TelemetryRecord.xtime),
        func.max(TelemetryRecord.xdist),
        func.avg(TelemetryRecord.gps_speed_kmh),
        func.max(TelemetryRecord.gps_speed_kmh),
        func.avg(TelemetryRecord.engine_speed_rpm),
        func.max(TelemetryRecord.engine_speed_rpm),
        func.avg(TelemetryRecord.throttle_pct),
        func.max(TelemetryRecord.coolant_temp_c),
        func.avg(func.abs(TelemetryRecord.az)),
        func.max(func.abs(TelemetryRecord.az)),
        func.max(TelemetryRecord.lap_number),
    ).filter(TelemetryRecord.session_id == session_id).one()

    if agg[0] == 0:
        raise HTTPException(status_code=404, detail="No telemetry data for this session yet.")

    return SessionMetrics(
        session_id=session_id,
        session_name=session.session_name,
        total_records=agg[0],
        duration_s=round((agg[2] or 0) - (agg[1] or 0), 3),
        total_distance_m=round(agg[3] or 0, 1),
        avg_speed_kmh=round(agg[4] or 0, 2),
        max_speed_kmh=round(agg[5] or 0, 2),
        avg_engine_rpm=round(agg[6] or 0, 1),
        max_engine_rpm=round(agg[7] or 0, 1),
        avg_throttle_pct=round(agg[8] or 0, 2),
        max_coolant_temp_c=round(agg[9] or 0, 1),
        avg_lateral_g=round(agg[10] or 0, 4),
        max_lateral_g=round(agg[11] or 0, 4),
        laps_recorded=agg[12],
    )
