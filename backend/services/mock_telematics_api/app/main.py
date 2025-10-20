from fastapi import FastAPI, HTTPException
import psycopg2
import os
import json
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = FastAPI(
    title="AxleOS - Mock Telematics API",
    description="A mock telematics API for vehicle telemetry data.",
    version="0.1.0"
)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("POSTGRES_DB", "db"),
        user=os.environ.get("POSTGRES_USER", "user"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        host="db",
        port="5432"
    )

# helps to serialize datetime objects to JSON
def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

@app.get("/telemetry/{vehicle_vin}")
def get_telemetry(vehicle_vin: str):
    try:
        con = get_db_connection()
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM historical_telemetry WHERE vehicle_vin = %s ORDER BY timestamp",
                (vin,)
            )
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail="Vehicle VIN not found")
            return json.loads(json.dumps(rows, default=json_serializer))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if con is not None:
            con.close()


@app.get("/maintenance_logs/{vehicle_vin}")
def get_logs_by_vin(vin: str):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM maintenance_logs WHERE vehicle_vin = %s ORDER BY failure_date",
                (vin,)
            )
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail="No maintenance logs found.")
            return json.loads(json.dumps(rows, default=json_serializer))
    except (Exception, psycopg2.DatabaseError) as error:
        raise HTTPException(status_code=500, detail=f"Database error: {error}")
    finally:
        if conn is not None:
            conn.close()

            