-- TimescaleDB migrations
-- Create hypertable for logs

-- Create logs table
CREATE TABLE IF NOT EXISTS logs (
    time TIMESTAMPTZ NOT NULL,
    source VARCHAR(100),
    host VARCHAR(255),
    level VARCHAR(20),
    message TEXT,
    metadata JSONB
);

-- Create index on time
CREATE INDEX IF NOT EXISTS idx_logs_time ON logs (time DESC);

-- Create index on source
CREATE INDEX IF NOT EXISTS idx_logs_source ON logs (source);

-- Create index on host
CREATE INDEX IF NOT EXISTS idx_logs_host ON logs (host);

-- Create index on level
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs (level);

-- Convert to hypertable
SELECT create_hypertable('logs', 'time', if_not_exists => TRUE);

-- Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW IF NOT EXISTS logs_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    source,
    level,
    COUNT(*) AS count
FROM logs
GROUP BY bucket, source, level;

-- Add retention policy (keep data for 90 days)
SELECT add_retention_policy('logs', INTERVAL '90 days', if_not_exists => TRUE);
