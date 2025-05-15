from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 19),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'stock_data_pipeline',
    default_args=default_args,
    description='A DAG to orchestrate stock data processing',
    schedule_interval=timedelta(days=1),
    catchup=False
)

# Task to ensure Kafka topic exists
ensure_kafka_topic = BashOperator(
    task_id='ensure_kafka_topic',
    bash_command='/opt/kafka/bin/kafka-topics.sh --create --if-not-exists --topic stock_data --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1',
    dag=dag
)

# Task to start the stock data generator
start_data_generator = BashOperator(
    task_id='start_data_generator',
    bash_command='python /opt/airflow/data_generator/stock_generator.py',
    dag=dag
)

# Task to process data with Spark
process_stock_data = BashOperator(
    task_id='process_stock_data',
    bash_command='spark-submit /opt/airflow/spark/stock_processor.py',
    dag=dag
)

# Set up task dependencies
ensure_kafka_topic >> start_data_generator >> process_stock_data 
