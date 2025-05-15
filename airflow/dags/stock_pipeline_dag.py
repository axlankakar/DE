from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 19),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1)
}

dag = DAG(
    'stock_data_pipeline',
    default_args=default_args,
    description='A DAG to orchestrate stock data processing',
    schedule_interval='@daily',
    catchup=False,
    tags=['stock', 'data', 'pipeline']
)

def check_kafka_health():
    """Check if Kafka is healthy"""
    try:
        from kafka import KafkaAdminClient
        admin_client = KafkaAdminClient(bootstrap_servers='kafka:9092')
        topics = admin_client.list_topics()
        logger.info(f"Kafka topics found: {topics}")
        admin_client.close()
        return True
    except Exception as e:
        logger.error(f"Kafka health check failed: {str(e)}")
        raise

# Task to check Kafka health
check_kafka = PythonOperator(
    task_id='check_kafka_health',
    python_callable=check_kafka_health,
    dag=dag
)

# Task to ensure Kafka topic exists
ensure_kafka_topic = BashOperator(
    task_id='ensure_kafka_topic',
    bash_command='kafka-topics.sh --create --if-not-exists --topic stock_data --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1',
    dag=dag
)

# Task to start the stock data generator
start_data_generator = BashOperator(
    task_id='start_data_generator',
    bash_command='python /opt/airflow/data_generator/stock_generator.py',
    dag=dag
)

# Task to process data with Spark
process_stock_data = SparkSubmitOperator(
    task_id='process_stock_data',
    application='/opt/airflow/spark/stock_processor.py',
    conn_id='spark_default',
    conf={
        'spark.master': 'spark://spark-master:7087',
        'spark.submit.deployMode': 'client',
        'spark.driver.memory': '1g',
        'spark.executor.memory': '2g',
        'spark.executor.cores': '2',
        'spark.jars.packages': 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,org.postgresql:postgresql:42.2.18'
    },
    dag=dag
)

# Set up task dependencies
check_kafka >> ensure_kafka_topic >> start_data_generator >> process_stock_data 
