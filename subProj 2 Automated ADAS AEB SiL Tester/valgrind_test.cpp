#include <iostream>

extern "C" {
int calculate_braking_force(double ego_speed, double obj_distance,
                            double speed_relative);
}

int main() {
  // Run 1,000,000 evaluations to securely trace memory allocs and prove
  // zero-leak capability
  for (int i = 0; i < 1000000; i++) {
    calculate_braking_force(50.0, 10.0, 36.0);
    calculate_braking_force(120.0, 150.0, 50.0);
    calculate_braking_force(100.0, 10.0, 72.0); // Will trigger flush
  }
  std::cout << "Valgrind test complete executing 3,000,000 cycles."
            << std::endl;
  return 0;
}
