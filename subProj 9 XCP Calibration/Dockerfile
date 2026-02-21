FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Explicitly add the current directory to PYTHONPATH so pytest can find modules
ENV PYTHONPATH=/app

CMD ["pytest", "tests/test_xcp_calibration.py", "-v", "--html=report.html", "--self-contained-html"]
