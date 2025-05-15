import json
import random
from datetime import datetime
from time import sleep
from kafka import KafkaProducer

def create_producer():
    return KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

def generate_stock_data():
    stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'AMD', 'INTC']
    base_prices = {
        'AAPL': 150, 'GOOGL': 2800, 'MSFT': 300, 'AMZN': 3300,
        'META': 300, 'TSLA': 900, 'NVDA': 250, 'NFLX': 500,
        'AMD': 100, 'INTC': 50
    }
    
    while True:
        for symbol in stocks:
            base_price = base_prices[symbol]
            # Generate random price movement
            price_change = random.uniform(-0.02, 0.02)  # -2% to +2%
            current_price = base_price * (1 + price_change)
            base_prices[symbol] = current_price  # Update base price
            
            data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'price': round(current_price, 2),
                'volume': random.randint(1000, 100000),
                'change': round(price_change * 100, 2)  # Convert to percentage
            }
            
            yield data

def main():
    producer = create_producer()
    generator = generate_stock_data()
    
    while True:
        try:
            data = next(generator)
            producer.send('stock_data', value=data)
            print(f"Sent data: {data}")
            sleep(1)  # Send data every second
        except Exception as e:
            print(f"Error sending data: {str(e)}")
            sleep(5)  # Wait before retrying

if __name__ == "__main__":
    main() 