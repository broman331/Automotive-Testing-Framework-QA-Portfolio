# Use a lightweight official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed (e.g., for virtual CAN, though we use python-can virtual interface)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run pytest directly and output HTML report to a mapped volume
# Using /app/reports so the user can easily map it: -v $(pwd)/reports:/app/reports
CMD ["pytest", "--html=/app/reports/report.html", "--self-contained-html"]
