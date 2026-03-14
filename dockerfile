FROM python:3.11-slim

WORKDIR /app

# Install dependencies first
RUN pip install --no-cache-dir fastapi>=0.128.8 fastapi-mcp>=0.4.0 mcp>=1.0.0 pyngrok>=7.5.0 python-dateutil>=2.9.0.post0 uvicorn>=0.39.0

# Copy application files
COPY . .

EXPOSE 8000

CMD ["python", "main.py"]