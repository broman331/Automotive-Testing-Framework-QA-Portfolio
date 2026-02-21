# Use Alpine or a slim Debian image for C++ compilation and Python execution
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install GCC, Make, Valgrind, and coverage tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    make \
    valgrind \
    lcov \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Compile the C++ shared library inside the Linux container
RUN make

# Give execution rights
RUN chmod +x run_advanced_tests.sh

# CMD will run the full suite: Pytest, GCOV, and Valgrind
CMD ["./run_advanced_tests.sh"]
