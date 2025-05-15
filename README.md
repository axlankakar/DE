# Stock Market Data Engineering Pipeline

This project implements an end-to-end data engineering pipeline for processing and analyzing stock market data. The pipeline ingests simulated real-time stock market data, processes it using various big data tools, and provides insights through a dashboard.

## Architecture

```
                                                     ┌─────────────┐
                                                     │             │
┌─────────────┐     ┌─────────────┐    ┌──────┐    │  PostgreSQL │
│  Stock Data │────>│    Kafka    │───>│ Spark │───>│  Database   │
│  Generator  │     │   Broker    │    │       │    │             │
└─────────────┘     └─────────────┘    └──────┘    └─────────────┘
                                                           │
                                                           │
                                                    ┌──────▼──────┐
                                                    │  Dashboard  │
                                                    │             │
                                                    └─────────────┘
```

## Components

1. **Data Generator**: Python script to simulate real-time stock market data
2. **Apache Kafka**: Message broker for streaming data
3. **Apache Spark**: Data processing engine for real-time analytics
4. **Apache Airflow**: Workflow orchestration
5. **PostgreSQL**: Data storage
6. **Dashboard**: Simple web interface for visualizations

## Setup Instructions

1. Install Docker and Docker Compose
2. Clone this repository
3. Run `docker-compose up -d` to start all services
4. Access the dashboard at http://localhost:8050

## Project Structure

```
.
├── airflow/                 # Airflow DAGs and configurations
├── data_generator/         # Stock data simulation scripts
├── spark/                  # Spark processing jobs
├── dashboard/             # Web dashboard
├── sql/                   # Database schemas and queries
├── docker/                # Dockerfile for each service
├── docker-compose.yml     # Docker services configuration
└── README.md             # Project documentation
```

## Technologies Used

- Python 3.9
- Apache Kafka
- Apache Spark
- Apache Airflow
- PostgreSQL
- Docker & Docker Compose
- Plotly Dash (for dashboard)

## Data Flow

1. The data generator simulates real-time stock market data for multiple stocks
2. Data is published to Kafka topics
3. Spark Streaming consumes data from Kafka and performs:
   - Data cleaning and validation
   - Calculating moving averages
   - Detecting price anomalies
4. Processed data is stored in PostgreSQL
5. Dashboard visualizes the data in real-time

## Running the Pipeline

1. Start all services:
```bash
docker-compose up -d
```

2. Check service status:
```bash
docker-compose ps
```

3. Access components:
- Airflow: http://localhost:8080
- Dashboard: http://localhost:8050
- Kafka Manager: http://localhost:9000

## Monitoring and Maintenance

- Logs can be viewed using `docker-compose logs -f [service_name]`
- Airflow provides a web interface for monitoring DAG runs
- Kafka Manager allows monitoring of Kafka topics and consumers

## Academic Integrity Statement

This project is my original work. All external libraries and resources used are properly cited in the requirements.txt file and throughout the codebase where applicable.

## Resources and Citations

1. Apache Kafka Documentation: https://kafka.apache.org/documentation/
2. Apache Spark Documentation: https://spark.apache.org/docs/latest/
3. Apache Airflow Documentation: https://airflow.apache.org/docs/
4. Python yfinance library: https://pypi.org/project/yfinance/
5. Plotly Dash Documentation: https://dash.plotly.com/ 