import os
import pandas as pd
import psycopg2
from io import StringIO
import time
import numpy as np

def generate_pre_failure_data(vin, end_time, odometer_start):
    #Generates telemetry data simulating an impending coolant system failure.
    print(f"Generating pre-failure data for VIN: {vin}")
    timestamps = pd.to_datetime(pd.date_range(end=end_time, periods=720, freq='T')) # 12 hours of data
    data = []
    # Simulate a subtle but steady increase in coolant temp over the last 6 hours
    coolant_temps = np.concatenate([
        np.random.normal(90, 1.5, 360), # Normal operation
        np.linspace(92, 105, 360) + np.random.normal(0, 0.5, 360) # Degradation period
    ])
    for i, ts in enumerate(timestamps):
        data.append({
            'vehicle_vin': vin,
            'timestamp': ts,
            'odometer': odometer_start + i * 2,
            'speed': np.random.uniform(60, 80),
            'rpm': np.random.uniform(1800, 2500),
            'throttle': np.random.uniform(0.4, 0.7),
            'engine_coolant_temp': coolant_temps[i],
            'engine_load': np.random.uniform(50, 70),
            'fuel_trim': np.random.uniform(-2, 2),
            'battery_voltage': np.random.uniform(13.8, 14.2),
            'ambient_air_temp': 25.0
        })
    return pd.DataFrame(data)

def generate_normal_data(vin, end_time, odometer_start):
    """Generates normal vehicle operation telemetry."""
    print(f"Generating normal operating data for VIN: {vin}")
    timestamps = pd.to_datetime(pd.date_range(end=end_time, periods=500, freq='T'))
    data = []
    for i, ts in enumerate(timestamps):
        data.append({
            'vehicle_vin': vin,
            'timestamp': ts,
            'odometer': odometer_start + i * 2,
            'speed': np.random.uniform(55, 75),
            'rpm': np.random.uniform(1600, 2200),
            'throttle': np.random.uniform(0.3, 0.6),
            'engine_coolant_temp': np.random.normal(90, 1.5),
            'engine_load': np.random.uniform(40, 60),
            'fuel_trim': np.random.uniform(-1, 1),
            'battery_voltage': np.random.uniform(13.9, 14.3),
            'ambient_air_temp': 22.0
        })
    return pd.DataFrame(data)


def bulk_insert_df(conn, df, table_name):
    #Inserts a DataFrame into the specified table using PostgreSQL COPY for efficiency.
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(
            sql=f"COPY {table_name}({','.join(df.columns)}) FROM STDIN WITH (FORMAT CSV)",
            file=buffer
        )
    conn.commit()


def seed_database():
    #Seeds the PostgreSQL database with generated telemetry and maintenance log data.
    print("Starting database seeding process...")
    db_name = os.environ.get("POSTGRES_DB", "db")
    db_user = os.environ.get("POSTGRES_USER", "user")
    db_password = os.environ.get("POSTGRES_PASSWORD", "password")
    db_host = "db"
    db_port = "5432"

    conn = None
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
            print("Successfully connected to the database.")
            break
        except psycopg2.OperationalError:
            print("Could not connect to database. Retrying...")
            retries -= 1
            time.sleep(5)

    if not conn:
        print("Failed to connect to the database. Exiting.")
        return

    try:
        # --- 1. Generate Data ---
        failure_time = pd.to_datetime('2023-10-28 12:00:00')
        # Vehicle 1: The one that will fail
        df_failure = generate_pre_failure_data('VIN001', failure_time, 85000)
        # Vehicle 2: A healthy vehicle for comparison
        df_normal = generate_normal_data('VIN002', failure_time, 62000)

        # --- 2. Create Maintenance Log Entry ---
        maintenance_data = {
            'vehicle_vin': ['VIN001'],
            'failure_date': [failure_time],
            'odometer_at_failure': [df_failure['odometer'].max()],
            'failed_component': ['water_pump'],
            'failure_notes': ['Vehicle reported overheating. Coolant leak found at water pump housing.']
        }
        df_logs = pd.DataFrame(maintenance_data)

        # --- 3. Insert Data into Database ---
        print("Inserting telemetry data...")
        bulk_insert_df(conn, df_failure, 'historical_telemetry')
        bulk_insert_df(conn, df_normal, 'historical_telemetry')
        print("Inserting maintenance logs...")
        bulk_insert_df(conn, df_logs, 'maintenance_logs')

        print("Database seeding complete.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error seeding database: {error}")
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    seed_database()