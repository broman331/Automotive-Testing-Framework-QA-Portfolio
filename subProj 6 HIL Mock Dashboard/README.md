# subProj 6: HIL Mock Dashboard (PyQt5)

## Overview
Automotive Quality Assurance heavily relies on Custom Test Tooling to interact with Simulation models (Hardware-in-the-Loop or Software-in-the-Loop). Specifically, QA engineers need visual dashboards to manually inject faults (like triggering ABS failure states or cutting communication nodes) and visualize the ensuing system reactions.

This project demonstrates the ability to build robust, Model-View-Controller (MVC) based `PyQt5` graphical interfaces. Crucially, it demonstrates that **Custom QA Tooling is held to the same rigorous testing standards as production code**.

The entire graphical interface is automatically driven and tested headlessly via `pytest-qt` in a CI/CD pipeline.

## Core Architecture
1. **Backend Simulation (`vehicle_sim.py`)**: A pure-Python physics loop calculating engine RPM, ground speed, and handling hardware states.
2. **PyQt5 Frontend (`dashboard.py`)**: A graphical user interface (GUI) rendering telemetry (Labels), user overrides (Sliders), and fault injection panels (Buttons).
3. **Automated GUI Testing (`tests/test_ui.py`)**: A `pytest-qt` suite that dynamically boots the UI and programmatically simulates mouse clicks and slider drags, asserting that the underlying physics engine reacts correctly.

## Headless CI/CD Automation
The `pytest-qt` suite is integrated into GitHub Actions (`.github/workflows/ci_subproj6.yml`). Because Ubuntu GitHub Runners do not have monitors, the pipeline installs `Xvfb` (X Virtual Framebuffer) to create a headless graphical environment, allowing Qt to render in memory while the automated tests click the invisible menus.

## Setup & Execution

### Running the Dashboard Locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python dashboard.py
```

### Running the Automated Qt Test Suite
```bash
export QT_QPA_PLATFORM=offscreen   # Speeds up local execution by suppressing the window draw
export PYTHONPATH=.
pytest tests/test_ui.py -v
```
