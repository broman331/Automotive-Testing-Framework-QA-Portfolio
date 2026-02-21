FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY autosar_nm_node.py .
COPY tests/ ./tests/

ENV PYTHONPATH=/app

CMD ["pytest", "tests/test_nm_statemachine.py", "-v", "--html=report.html", "--self-contained-html"]
