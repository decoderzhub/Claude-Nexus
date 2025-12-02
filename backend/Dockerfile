FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/core /app/data/world/objects \
    /app/data/memory/reflections /app/data/memory/conversations \
    /app/data/memory/insights /app/data/projects

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
