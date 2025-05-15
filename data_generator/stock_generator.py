import random
import time
import json
from datetime import datetime
from kafka import KafkaProducer

# List of sample stocks
STOCKS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "META",
    "TSLA", "NVDA", "NFLX", "AMD", "INTC"
]

class StockDataGenerator:
    def __init__(self, kafka_bootstrap_servers='kafka:9092'):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
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
        
        # Ensure all messages are sent
        self.producer.flush()

def main():
    generator = StockDataGenerator()
    print("Starting Stock Data Generator...")
    
    while True:
        try:
            generator.generate_stock_data()
            # Generate data every second
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping Stock Data Generator...")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main() 
