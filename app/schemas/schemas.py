from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


# ── Session Schemas ──────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    session_name: str
    vehicle_id: str
    driver: str
    track: str


class SessionResponse(BaseModel):
    id: int
    session_name: str
    vehicle_id: str
    driver: str
    track: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Telemetry Schemas — matched to Bosch DARAB FK07 export ──────────────────

class TelemetryRecordCreate(BaseModel):
    xtime: float                            # session elapsed time [s]
    xdist: Optional[float] = None           # session distance [m]
    az: Optional[float] = None              # lateral acceleration [g]
    coolant_temp_c: Optional[float] = None  # coolant temperature [°C]
    engine_speed_rpm: Optional[float] = None
    fuel_pressure_kpa: Optional[float] = None
    gps_speed_kmh: Optional[float] = None
    lapdist_m: Optional[float] = None       # distance into current lap [m]
    laptime_s: Optional[float] = None       # elapsed time in current lap [s]
    str_whl_angle_deg: Optional[float] = None
    throttle_pct: Optional[float] = None
    lap_number: Optional[int] = None        # assigned by importer

    @field_validator("gps_speed_kmh")
    @classmethod
    def speed_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("gps_speed_kmh must be >= 0")
        return v

    @field_validator("engine_speed_rpm")
    @classmethod
    def rpm_range(cls, v):
        if v is not None and not (0 <= v <= 20000):
            raise ValueError("engine_speed_rpm must be 0–20000")
        return v

    @field_validator("throttle_pct")
    @classmethod
    def throttle_range(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("throttle_pct must be 0–100")
        return v

    @field_validator("coolant_temp_c")
    @classmethod
    def coolant_range(cls, v):
        if v is not None and not (-40 <= v <= 200):
            raise ValueError("coolant_temp_c out of plausible range")
        return v


class TelemetryRecordResponse(TelemetryRecordCreate):
    id: int
    session_id: int
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ── Metrics Schema ────────────────────────────────────────────────────────────

class SessionMetrics(BaseModel):
    session_id: int
    session_name: str
    total_records: int
    duration_s: float
    total_distance_m: float
    avg_speed_kmh: float
    max_speed_kmh: float
    avg_engine_rpm: float
    max_engine_rpm: float
    avg_throttle_pct: float
    max_coolant_temp_c: float
    avg_lateral_g: float
    max_lateral_g: float
    laps_recorded: Optional[int] = None
