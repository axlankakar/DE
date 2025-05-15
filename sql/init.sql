\c postgres;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'stockdata') THEN
        CREATE DATABASE stockdata;
    END IF;
END
$$;

\c stockdata;

-- Create the stock_metrics table
CREATE TABLE IF NOT EXISTS stock_metrics (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    symbol VARCHAR(10) NOT NULL,
    avg_price DECIMAL(10, 2) NOT NULL,
    avg_volume INTEGER NOT NULL,
    avg_change DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_stock_metrics_symbol ON stock_metrics(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_metrics_window_start ON stock_metrics(window_start);

-- Create a view for the latest metrics
CREATE OR REPLACE VIEW latest_stock_metrics AS
SELECT DISTINCT ON (symbol)
    symbol,
    avg_price,
    avg_volume,
    avg_change,
    window_start as timestamp
FROM stock_metrics
ORDER BY symbol, window_start DESC; 
