from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String, unique=True, index=True)
    vehicle_id = Column(String, index=True)
    driver = Column(String)
    track = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    telemetry_records = relationship("TelemetryRecord", back_populates="session", cascade="all, delete")
