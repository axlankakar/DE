from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'stock_data_pipeline',
    default_args=default_args,
    description='Pipeline for processing stock market data',
    schedule_interval=timedelta(minutes=5),
    catchup=False
)

# Spark job to process stock data
process_stock_data = SparkSubmitOperator(
    task_id='process_stock_data',
    application='/opt/airflow/spark/process_stock_data.py',
    conn_id='spark_default',
    conf={
        'spark.master': 'spark://spark-master:7077',
        'spark.submit.deployMode': 'client'
    },
    packages='org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,org.postgresql:postgresql:42.2.18',
    dag=dag
)

process_stock_data 