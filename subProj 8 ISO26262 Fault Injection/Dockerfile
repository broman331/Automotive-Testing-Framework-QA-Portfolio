FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The Application Code
COPY fault_proxy.py .
COPY safety_ecu.py .
COPY tests/ ./tests/

ENV PYTHONPATH=/app

CMD ["pytest", "tests/test_iso26262_faults.py", "-v", "--html=report.html", "--self-contained-html"]
