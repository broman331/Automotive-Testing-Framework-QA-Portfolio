FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python codebase and tests
COPY capl_parser.py pytest.ini ./
COPY tests/ ./tests/

# Set the default entrypoint to run the test suite
CMD ["pytest", "tests/test_compiler.py", "-v", "--html=report.html", "--self-contained-html"]
