class VehicleSimulator:
    """
    Backend physics engine simulating a vehicle.
    Strictly decoupled from UI logic to ensure MVC testability.
    """
    def __init__(self):
        self.speed_kmh = 0.0
        self.rpm = 0.0
        self.throttle_percent = 0.0
        self.brake_failed = False
        
    def set_throttle(self, percent: float):
        """Sets the throttle pedal position [0-100]."""
        self.throttle_percent = max(0.0, min(100.0, percent))
        
    def inject_brake_failure(self):
        """Hardware fault injection: Brakes no longer decelerate the vehicle."""
        self.brake_failed = True
        
    def tick(self, dt_seconds: float = 0.1):
        """
        Calculates physics for one time-step. 
        In a real HIL environment, this would be tied to a hard real-time scheduler.
        """
        # Linear RPM calculation based on throttle
        target_rpm = self.throttle_percent * 60.0  # Max 6000 RPM
        
        # Simple smoothing function simulating engine inertia
        if self.rpm < target_rpm:
            self.rpm += 2000.0 * dt_seconds
        elif self.rpm > target_rpm:
            self.rpm -= 1500.0 * dt_seconds
            
        # Clamp RPM
        self.rpm = max(0.0, min(6000.0, self.rpm))
        
        # Speed derived from RPM (simplistic single-gear ratio for testing)
        target_speed = self.rpm * 0.03  # Max ~180 km/h @ 6000 RPM

        if self.speed_kmh < target_speed:
            self.speed_kmh += 10.0 * dt_seconds * (self.throttle_percent / 100.0)
        elif self.speed_kmh > target_speed:
            # If brakes failed, prevent normal rapid deceleration!
            if self.brake_failed and self.throttle_percent == 0:
                # Simulate coasting slowly without braking friction
                self.speed_kmh -= 1.0 * dt_seconds
            else:
                self.speed_kmh -= 15.0 * dt_seconds # Normal deceleration

        self.speed_kmh = max(0.0, self.speed_kmh)
