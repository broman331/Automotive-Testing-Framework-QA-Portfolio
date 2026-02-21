FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["pytest", "tests/test_secoc.py", "-v", "--html=report.html", "--self-contained-html"]
