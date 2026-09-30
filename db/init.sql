CREATE TABLE door_logs (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(10) NOT NULL,
    count_change INTEGER NOT NULL,
    total_occupancy INTEGER NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_door_recorded_at ON door_logs(recorded_at);

CREATE TABLE environment_logs (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    temperature_c NUMERIC(5,2) NOT NULL,
    humidity_percent NUMERIC(5,2) NOT NULL,
    light_lux NUMERIC(7,2) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_env_node_time ON environment_logs(node_id, recorded_at);

CREATE TABLE ac_status_logs (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    is_running BOOLEAN NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ac_node_time ON ac_status_logs(node_id, recorded_at);
