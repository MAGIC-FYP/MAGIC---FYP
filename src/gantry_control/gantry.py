import numpy as np
import RPi.GPIO as GPIO
import time

class GantryControl:
    def __init__(self, max_x: float, max_y: float, motor_radius: float = 0.95):
        # Pin definitions (using BCM numbering)
        self.DIR = 17   # Direction
        self.STEP = 27  # Step pulse
        self.EN = 22    # Enable (LOW = enabled)
        
        # Motor control parameters
        self.start_delay = 0.005   # 5ms (slow start)
        self.end_delay = 0.0015    # 1.5ms (max speed)
        self.pulse_width = 0.00005 # 50us
        
        # Physical parameters
        self.max_x = max_x                  # in cm
        self.max_y = max_y                  # in cm
        self.x_pos = 0                      # in cm
        self.x_vel = 0                      # in cm/s
        self.y_pos = 0                      # in cm
        self.y_vel = 0                      # in cm/s
        self.l_motor_pos = 0                # in rads
        self.l_motor_vel = 0                # in rads/s
        self.r_motor_pos = 0                # in rads
        self.r_motor_vel = 0                # in rads/s

        self.motor_radius = motor_radius    # in cm
        self.M = np.array([[1,0],[0,-1]])
        
        # Steps per revolution (typical for stepper motors)
        self.steps_per_rev = 200  # Adjust based on your motor
        self.cm_per_step = (2 * np.pi * self.motor_radius) / self.steps_per_rev

    def initialise(self):
        # Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.DIR, GPIO.OUT)
        GPIO.setup(self.STEP, GPIO.OUT)
        GPIO.setup(self.EN, GPIO.OUT)

        # Initialize pins
        GPIO.output(self.STEP, GPIO.LOW)
        GPIO.output(self.DIR, GPIO.LOW)
        GPIO.output(self.EN, GPIO.HIGH)  # Start disabled

        print("Pins initialized. Enabling driver...")
        time.sleep(1)

        # Enable driver
        GPIO.output(self.EN, GPIO.LOW)
        print("Driver enabled.")
        return True

    def move_steps(self, direction, num_steps, start_delay=None, end_delay=None, pulse_width=None):
        """Move stepper motor with acceleration/deceleration ramps"""
        if start_delay is None:
            start_delay = self.start_delay
        if end_delay is None:
            end_delay = self.end_delay
        if pulse_width is None:
            pulse_width = self.pulse_width
            
        GPIO.output(self.DIR, direction)
        
        accel_steps = min(10, num_steps // 3)
        decel_steps = min(10, num_steps // 3)
        const_steps = num_steps - accel_steps - decel_steps
        
        # Ensure we have enough steps for constant speed
        if const_steps < 50:
            accel_steps = (num_steps - 50) // 2
            decel_steps = (num_steps - 50) // 2
            const_steps = 50
        
        # Create acceleration ramp
        accel_delays = [start_delay + (end_delay - start_delay) * i / max(accel_steps - 1, 1) for i in range(accel_steps)]
        
        # Create deceleration ramp (reverse of acceleration)
        decel_delays = [end_delay + (start_delay - end_delay) * i / max(decel_steps - 1, 1) for i in range(decel_steps)]
        
        # Combine all delays
        all_delays = accel_delays + [end_delay] * const_steps + decel_delays
        
        for i in range(num_steps):
            GPIO.output(self.STEP, GPIO.HIGH)
            time.sleep(pulse_width)
            GPIO.output(self.STEP, GPIO.LOW)
            time.sleep(all_delays[i])
            
            # Update position tracking
            step_distance = self.cm_per_step * (1 if direction == GPIO.HIGH else -1)
            # This is a simplified update - in reality you'd need to track both motors
            self.x_pos += step_distance * 0.5  # Assuming equal contribution from both motors
            self.y_pos += step_distance * 0.5

    def move(self, x: float, y: float, vel: float):
        """Move to target position with specified velocity"""
        if not (x < self.max_x and y < self.max_y):
            raise ValueError("Target position out of bounds")
        
        delta_x = x - self.x_pos
        delta_y = y - self.y_pos
        distance = np.sqrt((delta_x**2) + (delta_y**2))
        
        if distance < 0.01:  # Already at target
            return
            
        # Calculate required motor movements
        angle = np.arctan2(delta_y, delta_x)
        a = vel * np.cos(angle)
        b = vel * np.sin(angle)
        d_dot = np.array([[a-b], [-a-b]])
        w_dot = (1/self.motor_radius) * self.M * d_dot
        
        # Convert to steps
        left_steps = int(abs(w_dot[0, 0]) * distance / vel / self.cm_per_step)
        right_steps = int(abs(w_dot[1, 0]) * distance / vel / self.cm_per_step)
        
        # Determine directions
        left_dir = GPIO.HIGH if w_dot[0, 0] > 0 else GPIO.LOW
        right_dir = GPIO.HIGH if w_dot[1, 0] > 0 else GPIO.LOW
        
        print(f"Moving to ({x:.2f}, {y:.2f}) - Left: {left_steps} steps, Right: {right_steps} steps")
        
        # Move both motors (simplified - in reality you'd need to coordinate them)
        if left_steps > 0:
            self.move_steps(left_dir, left_steps)
        if right_steps > 0:
            self.move_steps(right_dir, right_steps)
            
        # Update final position
        self.x_pos = x
        self.y_pos = y
        print(f"Move complete. Position: ({self.x_pos:.2f}, {self.y_pos:.2f})")
        
    def stop(self):
        """Stop all motors"""
        print("Stopping motors...")
        # The motors will stop when no more step pulses are sent
        self.x_vel = 0 
        self.y_vel = 0
        self.l_motor_vel = 0 
        self.r_motor_vel = 0

    def home(self):
        """Home the gantry to origin"""
        print("Homing to origin...")
        self.move(0, 0, 1.0)  # Move to origin at 1 cm/s
        print("Homing complete.")

    def get_status(self):
        """Get current status"""
        return {
            "x_pos": self.x_pos,
            "y_pos": self.y_pos,
            "l_motor_pos": self.l_motor_pos,
            "r_motor_pos": self.r_motor_pos,
            "l_motor_vel": self.l_motor_vel,
            "r_motor_vel": self.r_motor_vel
        }
        
    def cleanup(self):
        """Clean up GPIO pins"""
        print("Cleaning up GPIO...")
        GPIO.output(self.EN, GPIO.HIGH)  # Disable driver
        GPIO.cleanup()
        print("GPIO cleanup complete.")



gantry = GantryControl(max_x=600, max_y=450)
print(gantry.get_status())
gantry.move(10, 10, 1.0)
print(gantry.get_status())
gantry.stop()
print(gantry.get_status())
gantry.home()
print(gantry.get_status())
gantry.cleanup()

