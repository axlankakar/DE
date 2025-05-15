from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

def create_spark_session():
    return SparkSession.builder \
        .appName("StockDataProcessor") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0") \
        .getOrCreate()

def create_stock_schema():
    return StructType([
        StructField("timestamp", StringType(), True),
        StructField("symbol", StringType(), True),
        StructField("price", DoubleType(), True),
        StructField("volume", IntegerType(), True),
        StructField("change_percent", DoubleType(), True)
    ])

def process_stock_data(spark):
    # Define schema for stock data
    schema = create_stock_schema()
    
    # Read from Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "stock_data") \
        .load()
    
    # Parse JSON data
    parsed_df = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")
    
    # Convert timestamp string to timestamp type
    parsed_df = parsed_df.withColumn("timestamp", to_timestamp("timestamp"))
    
    # Calculate 5-minute moving average price for each stock
    window_duration = "5 minutes"
    moving_avg = parsed_df \
        .withWatermark("timestamp", window_duration) \
        .groupBy(
            window("timestamp", window_duration),
            "symbol"
        ) \
        .agg(
            avg("price").alias("avg_price"),
            avg("volume").alias("avg_volume"),
            avg("change_percent").alias("avg_change")
        )
    
    # Write to PostgreSQL
    def write_to_postgres(df, epoch_id):
        df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres:5432/stockdata") \
            .option("driver", "org.postgresql.Driver") \
            .option("dbtable", "stock_metrics") \
            .option("user", "airflow") \
            .option("password", "airflow") \
            .mode("append") \
            .save()
    
    # Start the streaming query
    query = moving_avg.writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("update") \
        .start()
    
    # Wait for the query to terminate
    query.awaitTermination()

def main():
    spark = create_spark_session()
    try:
        process_stock_data(spark)
    except KeyboardInterrupt:
        print("Stopping Spark Streaming...")
    finally:
        spark.stop()

if __name__ == "__main__":
    main() 