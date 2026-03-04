"""
import_darab.py
--------------
Parses a Bosch DARAB .txt export file and imports it into the Telemetry API.

Usage:
    python import_darab.py <path_to_file.txt> [--session-name NAME] [--driver NAME] [--track NAME] [--vehicle-id ID]

Example:
    python import_darab.py data/10_12_25_SCCA.txt --driver "Noah" --track "SCCA AutoX" --vehicle-id "FK07"
"""

import argparse
import re
import sys
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
BATCH_SIZE = 500  # records per POST /bulk call


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_darab_file(filepath: str) -> tuple[dict, list[dict]]:
    """
    Parse a Bosch DARAB tab-delimited export file.

    Returns:
        meta   - dict of header metadata (source file, time range)
        rows   - list of dicts, one per data row, with lap_number assigned
    """
    meta = {}
    rows = []

    with open(filepath, "r", errors="replace") as f:
        lines = f.readlines()

    # Parse comment header
    for line in lines:
        if line.startswith("# Data from source file"):
            match = re.search(r'"(.+)"', line)
            if match:
                meta["source_file"] = match.group(1)
        elif line.startswith("# where"):
            match = re.search(r"(\d+\.\d+) <= xtime <= (\d+\.\d+)", line)
            if match:
                meta["xtime_start"] = float(match.group(1))
                meta["xtime_end"] = float(match.group(2))
        elif line.startswith("xtime"):
            # Column header line — skip
            continue

    # Parse data rows
    data_lines = [
        l for l in lines
        if not l.startswith("#") and l.strip() and not l.startswith("xtime")
    ]

    print(f"  Found {len(data_lines):,} data rows. Assigning lap numbers...")

    prev_laptime = None
    current_lap = 1

    for line in data_lines:
        parts = line.split()
        if len(parts) != 11:
            continue  # skip malformed rows

        try:
            xtime          = float(parts[0])
            xdist          = float(parts[1])
            az             = float(parts[2])
            coolant_temp_c = float(parts[3])
            engine_rpm     = float(parts[4])
            fuel_pressure  = float(parts[5])
            gps_speed_kmh  = float(parts[6])
            lapdist_m      = float(parts[7])
            laptime_s      = float(parts[8])
            str_whl_angle  = float(parts[9])
            throttle_pct   = float(parts[10])
        except ValueError:
            continue  # skip any unparseable rows

        # Detect lap boundary: laptime resets to near 0 after being > 5s
        if prev_laptime is not None and laptime_s < 1.0 and prev_laptime > 5.0:
            current_lap += 1

        rows.append({
            "xtime":             xtime,
            "xdist":             xdist,
            "az":                az,
            "coolant_temp_c":    coolant_temp_c,
            "engine_speed_rpm":  engine_rpm,
            "fuel_pressure_kpa": fuel_pressure,
            "gps_speed_kmh":     gps_speed_kmh,
            "lapdist_m":         lapdist_m,
            "laptime_s":         laptime_s,
            "str_whl_angle_deg": str_whl_angle,
            "throttle_pct":      throttle_pct,
            "lap_number":        current_lap,
        })

        prev_laptime = laptime_s

    meta["laps_detected"] = current_lap
    return meta, rows


# ── API Helpers ───────────────────────────────────────────────────────────────

def create_session(session_name: str, vehicle_id: str, driver: str, track: str) -> int:
    payload = {
        "session_name": session_name,
        "vehicle_id":   vehicle_id,
        "driver":       driver,
        "track":        track,
    }
    res = requests.post(f"{BASE_URL}/sessions/", json=payload)
    if res.status_code == 409:
        print(f"  Session '{session_name}' already exists. Fetching existing session...")
        sessions = requests.get(f"{BASE_URL}/sessions/").json()
        for s in sessions:
            if s["session_name"] == session_name:
                return s["id"]
        raise RuntimeError("Could not find existing session.")
    res.raise_for_status()
    session_id = res.json()["id"]
    print(f"  Created session ID: {session_id}")
    return session_id


def ingest_batches(session_id: int, rows: list[dict]) -> int:
    total_inserted = 0
    total_batches = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        res = requests.post(f"{BASE_URL}/sessions/{session_id}/telemetry/bulk", json=batch)
        res.raise_for_status()
        inserted = res.json()["inserted"]
        total_inserted += inserted
        print(f"  Batch {batch_num}/{total_batches} — inserted {inserted} records ({total_inserted:,} total)")

    return total_inserted


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Import a Bosch DARAB export into the Telemetry API.")
    parser.add_argument("filepath",                          help="Path to the .txt DARAB export file")
    parser.add_argument("--session-name", default=None,      help="Session name (default: filename without extension)")
    parser.add_argument("--driver",       default="Unknown", help="Driver name")
    parser.add_argument("--track",        default="Unknown", help="Track / event name")
    parser.add_argument("--vehicle-id",   default="Unknown", help="Vehicle ID (e.g. FK07)")
    args = parser.parse_args()

    filepath = Path(args.filepath)
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    session_name = args.session_name or filepath.stem

    print(f"\n=== Bosch DARAB Importer ===")
    print(f"File:    {filepath}")
    print(f"Session: {session_name}")
    print(f"Driver:  {args.driver}")
    print(f"Track:   {args.track}")
    print(f"Vehicle: {args.vehicle_id}\n")

    # 1. Parse
    print("Step 1/3 — Parsing file...")
    meta, rows = parse_darab_file(str(filepath))
    print(f"  Parsed {len(rows):,} records across {meta['laps_detected']} laps")
    if "source_file" in meta:
        print(f"  Source: {meta['source_file']}")

    # 2. Create session
    print("\nStep 2/3 — Creating session via API...")
    session_id = create_session(session_name, args.vehicle_id, args.driver, args.track)

    # 3. Ingest
    print(f"\nStep 3/3 — Ingesting {len(rows):,} records in batches of {BATCH_SIZE}...")
    total = ingest_batches(session_id, rows)

    # 4. Pull metrics
    print(f"\n✓ Import complete — {total:,} records loaded.")
    print("\nFetching session metrics...")
    metrics = requests.get(f"{BASE_URL}/sessions/{session_id}/telemetry/metrics").json()
    print(f"""
  Session:          {metrics['session_name']}
  Total records:    {metrics['total_records']:,}
  Duration:         {metrics['duration_s']:.1f}s
  Total distance:   {metrics['total_distance_m']:,.0f}m
  Laps recorded:    {metrics['laps_recorded']}
  Max speed:        {metrics['max_speed_kmh']:.1f} km/h
  Avg speed:        {metrics['avg_speed_kmh']:.1f} km/h
  Max engine RPM:   {metrics['max_engine_rpm']:,.0f}
  Max coolant temp: {metrics['max_coolant_temp_c']:.1f}°C
  Avg throttle:     {metrics['avg_throttle_pct']:.1f}%
  Max lateral G:    {metrics['max_lateral_g']:.3f}g
""")


if __name__ == "__main__":
    main()
