from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id"), nullable=False)

    # Bosch DARAB columns — exact match to FK07 export format
    xtime = Column(Float, nullable=False)            # session elapsed time [s]
    xdist = Column(Float, nullable=True)             # session distance [m]
    az = Column(Float, nullable=True)                # lateral acceleration [g]
    coolant_temp_c = Column(Float, nullable=True)    # coolant temperature [°C]
    engine_speed_rpm = Column(Float, nullable=True)  # engine speed [rpm]
    fuel_pressure_kpa = Column(Float, nullable=True) # fuel pressure [kPa]
    gps_speed_kmh = Column(Float, nullable=True)     # GPS speed [km/h]
    lapdist_m = Column(Float, nullable=True)         # distance into current lap [m]
    laptime_s = Column(Float, nullable=True)         # elapsed lap time [s]
    str_whl_angle_deg = Column(Float, nullable=True) # steering wheel angle [°]
    throttle_pct = Column(Float, nullable=True)      # throttle position [%]

    # Derived field — assigned by importer
    lap_number = Column(Integer, nullable=True, index=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("TestSession", back_populates="telemetry_records")
