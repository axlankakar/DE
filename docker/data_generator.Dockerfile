FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY data_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY data_generator/generate_stock_data.py .

# Run the generator
CMD ["python", "generate_stock_data.py"] 