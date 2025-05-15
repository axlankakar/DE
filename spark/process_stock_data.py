from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

def create_spark_session():
    return SparkSession.builder \
        .appName("StockDataProcessing") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,org.postgresql:postgresql:42.2.18") \
        .getOrCreate()

def process_stock_data(spark):
    # Define schema for stock data
    schema = StructType([
        StructField("symbol", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("price", DoubleType(), True),
        StructField("volume", IntegerType(), True),
        StructField("change", DoubleType(), True)
    ])

    # Read from Kafka
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "stock_data") \
        .load()

    # Parse JSON data
    parsed_df = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # Calculate metrics using windowing
    window_duration = "5 minutes"
    metrics_df = parsed_df \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(
            window("timestamp", window_duration),
            "symbol"
        ) \
        .agg(
            avg("price").alias("avg_price"),
            avg("volume").cast("integer").alias("avg_volume"),
            avg("change").alias("avg_change")
        )

    # Write to PostgreSQL
    def write_to_postgres(df, epoch_id):
        df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres:5432/stockdata") \
            .option("dbtable", "stock_metrics") \
            .option("user", "airflow") \
            .option("password", "airflow") \
            .mode("append") \
            .save()

    # Start streaming query
    query = metrics_df \
        .writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("update") \
        .trigger(processingTime=window_duration) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    spark = create_spark_session()
    process_stock_data(spark) 