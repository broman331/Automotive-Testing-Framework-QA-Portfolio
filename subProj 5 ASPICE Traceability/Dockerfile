FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python codebase and requirements DB
COPY test_mock_app.py traceability_generator.py requirements.json pytest.ini conftest.py ./

# Set the default entrypoint to run the test suite and then the traceability engine
CMD ["sh", "-c", "pytest test_mock_app.py --junitxml=report.xml && python traceability_generator.py"]
