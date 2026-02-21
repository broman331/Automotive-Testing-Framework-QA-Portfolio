import pytest
from PyQt5.QtCore import Qt
from vehicle_sim import VehicleSimulator
from dashboard import MockDashboard

# -------------------------------------------------------------------
# Part 1: Backend Physics Logic Tests
# -------------------------------------------------------------------

def test_tc_601_default_initialization():
    """TC-601: Assert vehicle boots to 0 state."""
    sim = VehicleSimulator()
    assert sim.speed_kmh == 0.0
    assert sim.rpm == 0.0
    assert sim.brake_failed == False

def test_tc_602_signal_acceleration():
    """TC-602: Assert applying throttle accelerates the vehicle."""
    sim = VehicleSimulator()
    sim.set_throttle(100.0)
    
    # Tick 1 second
    for _ in range(10):
        sim.tick(0.1)
        
    assert sim.rpm > 1000.0
    assert sim.speed_kmh > 5.0

def test_tc_603_fault_overrides():
    """TC-603: Assert brake failure suppresses deceleration logic."""
    sim = VehicleSimulator()
    # Force some speed
    sim.speed_kmh = 100.0
    
    # Normal braking (throttle 0)
    sim.tick(0.1)
    normal_decel_speed = sim.speed_kmh
    assert normal_decel_speed < 100.0
    
    # Faulted braking
    sim.inject_brake_failure()
    sim.tick(0.1)
    fault_decel_speed = sim.speed_kmh
    assert fault_decel_speed > (normal_decel_speed - 15.0 * 0.1) # Decelerating MUCH slower

# -------------------------------------------------------------------
# Part 2: PyQt5 UI/Frontend Validation (pytest-qt)
# -------------------------------------------------------------------

@pytest.fixture
def app_window(qtbot):
    """Pytest-qt fixture to boot and automatically clean up the UI."""
    sim = VehicleSimulator()
    window = MockDashboard(sim)
    qtbot.addWidget(window)
    return window, sim

def test_tc_604_ui_initialization(app_window):
    """TC-604: Assert the UI text labels start at zero."""
    window, _ = app_window
    assert window.speed_label.text() == "Speed: 0 km/h"
    assert window.rpm_label.text() == "RPM: 0"
    assert window.fault_label.text() == "SYSTEM: OK"

def test_tc_605_slider_hardware_event(app_window, qtbot):
    """TC-605: Assert sliding the QSlider actively edits the backend state."""
    window, sim = app_window
    
    # Simulate an engineer dragging the slider to 50%
    window.throttle_slider.setValue(50)
    
    # The signal should instantly transmit to backend simulator
    assert sim.throttle_percent == 50.0

def test_tc_606_fault_injection_click(app_window, qtbot):
    """TC-606: Assert clicking the UI button toggles the backend fault bool AND edits the UI label."""
    window, sim = app_window
    
    # Simulate a left-mouse click on the red fault button
    qtbot.mouseClick(window.inject_btn, Qt.LeftButton)
    
    # Assert backend is corrupted
    assert sim.brake_failed == True
    
    # Assert UI turned red
    assert window.fault_label.text() == "SYSTEM: BRAKE FAILURE"
    assert "color: red" in window.fault_label.styleSheet()
