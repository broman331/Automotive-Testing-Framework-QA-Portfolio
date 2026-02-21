FROM python:3.11-slim

# Install system dependencies for headless Qt, xvfb, and the native PyQt5 linux library (to prevent building Qt from source on ARM64)
RUN apt-get update && apt-get install -y \
    xvfb \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    python3-pyqt5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
# Strip out PyQt5 since we installed it natively via APT, then pip install the rest
RUN grep -v "PyQt5" requirements.txt > req_docker.txt && pip install --no-cache-dir -r req_docker.txt

# Copy application files and tests suite
COPY vehicle_sim.py dashboard.py ./
COPY tests/ ./tests/

# Set PYTHONPATH to the app directory
ENV PYTHONPATH=/app

# Execute tests headlessly via X virtual framebuffer
CMD ["xvfb-run", "--auto-servernum", "pytest", "tests/test_ui.py", "-v", "--html=report.html"]
