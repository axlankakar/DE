import random
import time
import json
from datetime import datetime
from kafka import KafkaProducer
import logging
import os
from kafka.errors import NoBrokersAvailable
from time import sleep

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of sample stocks
STOCKS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "META",
    "TSLA", "NVDA", "NFLX", "AMD", "INTC"
]

def create_producer(max_retries=5, retry_interval=5):
    """Create Kafka producer with retry logic"""
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                api_version=(0, 10, 1)
            )
            logger.info("Successfully connected to Kafka")
            return producer
        except NoBrokersAvailable:
            if attempt < max_retries - 1:
                logger.warning(f"Could not connect to Kafka. Retrying in {retry_interval} seconds...")
                sleep(retry_interval)
            else:
                logger.error("Failed to connect to Kafka after maximum retries")
                raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Kafka: {str(e)}")
            raise

class StockDataGenerator:
    def __init__(self):
        self.producer = create_producer()
        
        # Initialize base prices for stocks
        self.base_prices = {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
            "MSFT": 300.0,
            "AMZN": 3300.0,
            "META": 330.0,
            "TSLA": 900.0,
            "NVDA": 250.0,
            "NFLX": 500.0,
            "AMD": 100.0,
            "INTC": 50.0
        }
        
        # Volatility for each stock (percentage)
        self.volatility = {stock: random.uniform(0.5, 2.0) for stock in STOCKS}

    def generate_price_change(self, stock):
        volatility = self.volatility[stock]
        change_percent = random.gauss(0, volatility)
        return change_percent / 100.0

    def generate_stock_data(self):
        timestamp = datetime.now().isoformat()
        
        for stock in STOCKS:
            try:
                # Calculate new price
                price_change = self.generate_price_change(stock)
                self.base_prices[stock] *= (1 + price_change)
                
                # Generate trading volume
                volume = int(random.gauss(100000, 50000))
                if volume < 0:
                    volume = 0
                
                data = {
                    "timestamp": timestamp,
                    "symbol": stock,
                    "price": round(self.base_prices[stock], 2),
                    "volume": volume,
                    "change_percent": round(price_change * 100, 2)
                }
                
                # Send to Kafka
                self.producer.send('stock_data', value=data)
                logger.debug(f"Sent data for {stock}: {data}")
            except Exception as e:
                logger.error(f"Error generating data for {stock}: {str(e)}")
        
        # Ensure all messages are sent
        self.producer.flush()

def main():
    generator = None
    while True:
        try:
            if generator is None:
                generator = StockDataGenerator()
            generator.generate_stock_data()
            # Generate data every second
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping Stock Data Generator...")
            if generator and generator.producer:
                generator.producer.close()
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            if generator and generator.producer:
                generator.producer.close()
            generator = None
            time.sleep(5)  # Wait before retrying
            continue

if __name__ == "__main__":
    main() 
