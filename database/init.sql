
SET client_min_messages TO WARNING;

CREATE OR REPLACE FUNCTION random_between(low double precision, high double precision)
RETURNS double precision AS
$$
BEGIN
   RETURN random() * (high - low) + low;
END;
$$ LANGUAGE plpgsql;

-- Table to store detailed, second-by-second vehicle sensor data
CREATE TABLE historical_telemetry (
    id SERIAL PRIMARY KEY,
    vehicle_vin VARCHAR(17) NOT NULL,
    "timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,
    odometer INTEGER,
    -- Powertrain
    speed REAL,
    rpm REAL,
    throttle REAL,
    engine_coolant_temp REAL,
    engine_load REAL,
    fuel_trim REAL,
    -- Electrical
    battery_voltage REAL,
    -- Environment
    ambient_air_temp REAL
);

-- Table to log actual failure and maintenance events
CREATE TABLE maintenance_logs (
    id SERIAL PRIMARY KEY,
    vehicle_vin VARCHAR(17) NOT NULL,
    failure_date TIMESTAMP WITH TIME ZONE NOT NULL,
    odometer_at_failure INTEGER,
    failed_component VARCHAR(100) NOT NULL,
    failure_notes TEXT
);

-- Create an index for faster lookups by VIN and timestamp
CREATE INDEX idx_telemetry_vin_time ON historical_telemetry (vehicle_vin, "timestamp" DESC);
CREATE INDEX idx_logs_vin ON maintenance_logs (vehicle_vin);