import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton
from PyQt5.QtCore import Qt, QTimer
from vehicle_sim import VehicleSimulator

class MockDashboard(QMainWindow):
    """
    PyQt5 GUI Front-end. Connects visual widgets to the backend VehicleSimulator.
    Designed for automated CI/CD clicking via pytest-qt.
    """
    def __init__(self, simulator: VehicleSimulator):
        super().__init__()
        self.sim = simulator
        self.init_ui()
        
        # Setup Qt Timer to call tick() every 100ms
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(100)

    def init_ui(self):
        self.setWindowTitle('Automotive HIL Mock Dashboard')
        self.setFixedSize(400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Labels for Telemetry
        self.speed_label = QLabel("Speed: 0 km/h")
        self.speed_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.rpm_label = QLabel("RPM: 0")
        self.rpm_label.setStyleSheet("font-size: 20px;")
        self.steering_label = QLabel("Steering: 0°")
        self.steering_label.setStyleSheet("font-size: 20px;")
        
        self.fault_label = QLabel("SYSTEM: OK")
        self.fault_label.setStyleSheet("color: green; font-weight: bold;")

        # Throttle Slider
        slider_layout = QHBoxLayout()
        slider_label = QLabel("Throttle:")
        self.throttle_slider = QSlider(Qt.Horizontal)
        self.throttle_slider.setMinimum(0)
        self.throttle_slider.setMaximum(100)
        self.throttle_slider.setValue(0)
        self.throttle_slider.valueChanged.connect(self.on_throttle_changed)
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.throttle_slider)

        # Steering Slider
        steer_layout = QHBoxLayout()
        steer_label = QLabel("Steering:")
        self.steering_slider = QSlider(Qt.Horizontal)
        self.steering_slider.setMinimum(-100)
        self.steering_slider.setMaximum(100)
        self.steering_slider.setValue(0)
        self.steering_slider.valueChanged.connect(self.on_steering_changed)
        steer_layout.addWidget(steer_label)
        steer_layout.addWidget(self.steering_slider)

        # Fault Injection Buttons
        self.inject_btn = QPushButton("Inject Brake Failure")
        self.inject_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.inject_btn.clicked.connect(self.on_inject_brake_fault)

        self.overheat_btn = QPushButton("Inject Engine Overheat")
        self.overheat_btn.setStyleSheet("background-color: darkorange; color: white; font-weight: bold;")
        self.overheat_btn.clicked.connect(self.on_inject_overheat_fault)

        # Assembly
        main_layout.addWidget(self.speed_label)
        main_layout.addWidget(self.rpm_label)
        main_layout.addWidget(self.steering_label)
        main_layout.addWidget(self.fault_label)
        main_layout.addLayout(slider_layout)
        main_layout.addLayout(steer_layout)
        main_layout.addWidget(self.inject_btn)
        main_layout.addWidget(self.overheat_btn)

        central_widget.setLayout(main_layout)

    def on_throttle_changed(self, value):
        self.sim.set_throttle(value)
        
    def on_steering_changed(self, value):
        self.sim.set_steering(value)
        
    def on_inject_brake_fault(self):
        self.sim.inject_brake_failure()
        self.fault_label.setText("SYSTEM: BRAKE FAILURE")
        self.fault_label.setStyleSheet("color: red; font-weight: bold;")
        self.inject_btn.setEnabled(False)

    def on_inject_overheat_fault(self):
        self.sim.inject_engine_overheat()
        self.fault_label.setText("SYSTEM: ENGINE OVERHEAT")
        self.fault_label.setStyleSheet("color: darkorange; font-weight: bold;")
        self.overheat_btn.setEnabled(False)

    def update_simulation(self):
        """Tick the backend and update the frontend labels."""
        self.sim.tick(dt_seconds=0.1)
        speed = int(self.sim.speed_kmh)
        self.speed_label.setText(f"Speed: {speed} km/h")
        self.rpm_label.setText(f"RPM: {int(self.sim.rpm)}")
        self.steering_label.setText(f"Steering: {int(self.sim.steering_angle)}°")
        
        # Dynamic Speed Warning UI
        if speed > 120:
            self.speed_label.setStyleSheet("font-size: 24px; font-weight: bold; color: red;")
        else:
            self.speed_label.setStyleSheet("font-size: 24px; font-weight: bold; color: black;")

if __name__ == '__main__':
    app = QApplication(sys.path)
    simulator = VehicleSimulator()
    window = MockDashboard(simulator)
    window.show()
    sys.exit(app.exec_())
