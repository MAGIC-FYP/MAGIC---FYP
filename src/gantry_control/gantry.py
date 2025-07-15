import numpy as np
import RPi.GPIO as GPIO
import time

class GantryControl:
    def __init__(self, max_x: float, max_y: float, motor_radius: float = 0.95):
        # Pin definitions (using BCM numbering)
        self.L_DIR = 17   # Direction
        self.L_STEP = 27  # Step pulse
        self.L_EN = 22    # Enable (LOW = enabled)
        self.R_DIR = 25   # Direction
        self.R_STEP = 24  # Step pulse
        self.R_EN = 23    # Enable (LOW = enabled)
        
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
        self.cm_per_step = 0.011134999999999999#(2 * np.pi * self.motor_radius) / self.steps_per_rev



    def initialise(self):
        # Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.L_DIR, GPIO.OUT)
        GPIO.setup(self.L_STEP, GPIO.OUT)
        GPIO.setup(self.L_EN, GPIO.OUT)
        GPIO.setup(self.R_DIR, GPIO.OUT)
        GPIO.setup(self.R_STEP, GPIO.OUT)
        GPIO.setup(self.R_EN, GPIO.OUT)
        GPIO.setup(6, GPIO.OUT)

        # Initialize pins
        GPIO.output(self.L_STEP, GPIO.LOW)
        GPIO.output(6, GPIO.HIGH)
        GPIO.output(self.L_DIR, GPIO.LOW)
        GPIO.output(self.L_EN, GPIO.HIGH)  
        GPIO.output(self.R_STEP, GPIO.LOW)
        GPIO.output(self.R_DIR, GPIO.LOW)
        GPIO.output(self.R_EN, GPIO.HIGH)  # Start disabled

        print("Pins initialized. Enabling driver...")
        time.sleep(1)

        # Enable driver
        GPIO.output(self.L_EN, GPIO.LOW)
        GPIO.output(self.R_EN, GPIO.LOW)
        print("Driver enabled.")
        return True

    def move_steps(self, direction_left, direction_right, num_steps_left, num_steps_right, start_delay=None, end_delay=None, pulse_width=None):
        """Move stepper motor with acceleration/deceleration ramps"""
        if start_delay is None:
            start_delay = self.start_delay
        if end_delay is None:
            end_delay = self.end_delay
        if pulse_width is None:
            pulse_width = self.pulse_width
            
        GPIO.output(self.L_DIR, direction_left)
        GPIO.output(self.R_DIR, direction_right)
        
        accel_steps_left = min(10, num_steps_left // 3)
        decel_steps_left = min(10, num_steps_left // 3)
        const_steps_left = num_steps_left - accel_steps_left - decel_steps_left

        accel_steps_right = min(10, num_steps_right // 3)
        decel_steps_right = min(10, num_steps_right // 3)
        const_steps_right = num_steps_right - accel_steps_right - decel_steps_right
        
        # Ensure we have enough steps for constant speed
        if const_steps_left < 50:
            accel_steps_left = (num_steps_left - 50) // 2
            decel_steps_left = (num_steps_left - 50) // 2
            const_steps_left = 50

        if const_steps_right < 50:
            accel_steps_right = (num_steps_right - 50) // 2
            decel_steps_right = (num_steps_right - 50) // 2
            const_steps_right = 50
        
        # Create acceleration ramp
        accel_delays_left = [start_delay + (end_delay - start_delay) * i / max(accel_steps_left - 1, 1) for i in range(accel_steps_left)]
        accel_delays_right = [start_delay + (end_delay - start_delay) * i / max(accel_steps_right - 1, 1) for i in range(accel_steps_right)]
        
        # Create deceleration ramp (reverse of acceleration)
        decel_delays_left = [end_delay + (start_delay - end_delay) * i / max(decel_steps_left - 1, 1) for i in range(decel_steps_left)]
        decel_delays_right = [end_delay + (start_delay - end_delay) * i / max(decel_steps_right - 1, 1) for i in range(decel_steps_right)]
        
        # Combine all delays
        all_delays_left = accel_delays_left + [end_delay] * const_steps_left + decel_delays_left
        all_delays_right = accel_delays_right + [end_delay] * const_steps_right + decel_delays_right
        
        
        left_steps = num_steps_left
        right_steps = num_steps_right
        max_steps = max(left_steps, right_steps)

        left_counter = 0
        right_counter = 0

        for i in range(max_steps):
            if (i * left_steps) // max_steps > left_counter:
                GPIO.output(self.L_STEP, GPIO.HIGH)
                time.sleep(self.pulse_width)
                GPIO.output(self.L_STEP, GPIO.LOW)
                time.sleep(all_delays_left[left_counter] if left_counter < len(all_delays_left) else 0)
                left_counter += 1

            if (i * right_steps) // max_steps > right_counter:
                GPIO.output(self.R_STEP, GPIO.HIGH)
                time.sleep(self.pulse_width)
                GPIO.output(self.R_STEP, GPIO.LOW)
                time.sleep(all_delays_right[right_counter] if right_counter < len(all_delays_right) else 0)
                right_counter += 1

            
            # Update position tracking
            step_distance_left = self.cm_per_step * (1 if direction_left == GPIO.HIGH else -1)
            step_distance_right = self.cm_per_step * (1 if direction_right == GPIO.HIGH else -1)
            # This is a simplified update - in reality you'd need to track both motors
            self.x_pos += step_distance_left * 0.5  # Assuming equal contribution from both motors
            self.y_pos += step_distance_right * 0.5

    

        return True

    def move(self, x: float, y: float, vel: float):
        """Move to target position with specified velocity"""
        if not (x < self.max_x and y < self.max_y):
            raise ValueError("Target position out of bounds")
        
        delta_x = x - self.x_pos
        delta_y = y - self.y_pos
        distance = np.sqrt((delta_x**2) + (delta_y**2))
        print(f"Distance: {distance}, Delta x: {delta_x}, Delta y: {delta_y}")
        
        if distance < 0.01:  # Already at target
            return
            
        # Calculate required motor movements
        # angle = np.arctan2(delta_y, delta_x)
        # a = vel * np.cos(angle)
        # b = vel * np.sin(angle)
        # d_dot = np.array([[a-b], [-a-b]])
        # w_dot = (1/self.motor_radius) * self.M * d_dot
        
        # # Convert to steps
        # left_steps = int(abs(w_dot[0, 0]) * distance / self.cm_per_step)
        # right_steps = int(abs(w_dot[1, 0]) * distance / self.cm_per_step)


        
        left_steps = int(abs(delta_x-delta_y) / self.cm_per_step)
        right_steps = int(abs(-delta_x-delta_y) / self.cm_per_step)

        # Determine directions
        left_dir = GPIO.HIGH if  delta_x-delta_y> 0 else GPIO.LOW
        right_dir = GPIO.HIGH if  -delta_x-delta_y> 0 else GPIO.LOW
        
        print(f"Moving to ({x:.2f}, {y:.2f}) - Left: {left_steps} steps, Right: {right_steps} steps")
        
        # Move both motors (simplified - in reality you'd need to coordinate them)
        if left_steps+right_steps > 0:
            self.move_steps(left_dir, right_dir, left_steps, right_steps)
        
            
        # Update final position
        self.x_pos = x
        self.y_pos = y
        #print(f"Move complete. Position: ({self.x_pos:.2f}, {self.y_pos:.2f})")
        
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
        GPIO.output(self.L_EN, GPIO.HIGH)  # Disable left motor
        GPIO.output(self.R_EN, GPIO.HIGH)  # Disable right motor
        GPIO.cleanup()
        print("GPIO cleanup complete.")


    def test_stepper(self):
        GPIO.output(self.R_STEP, GPIO.HIGH)
        time.sleep(self.pulse_width)
        GPIO.output(self.R_STEP, GPIO.LOW)
        for i in range(100):
            GPIO.output(self.R_STEP, GPIO.HIGH)
            time.sleep(self.pulse_width)
            GPIO.output(self.R_STEP, GPIO.LOW)
            time.sleep(0.005)

        for i in range(100):
            GPIO.output(self.L_STEP, GPIO.HIGH)
            time.sleep(self.pulse_width)
            GPIO.output(self.L_STEP, GPIO.LOW)
            time.sleep(0.005)
    
    def calibrate(self):
        """Calibrate the gantry"""
        print("Calibrating gantry...")
        self.move(0, 0, 0.3)
        for i in range(500):
            GPIO.output(self.R_STEP, GPIO.HIGH)
            time.sleep(self.pulse_width)
            GPIO.output(self.R_STEP, GPIO.LOW)
            time.sleep(0.005)

        
        cm = float(input("Enter cm to moved: "))
        cm_per_step = ((cm*np.sqrt(2)) / (500))
        self.x_pos += -cm/np.sqrt(2)
        self.y_pos += cm/np.sqrt(2)
        
        print(f"cm_per_step: {self.cm_per_step}")
        for i in range(500):
            GPIO.output(self.L_STEP, GPIO.HIGH)
            time.sleep(self.pulse_width)
            GPIO.output(self.L_STEP, GPIO.LOW)
            time.sleep(0.005)
        
        self.x_pos += cm/np.sqrt(2)
        self.y_pos += -cm/np.sqrt(2)
        yN = input(f"is this {cm}cm y/n? ")
        if yN == "y":
            self.cm_per_step = cm_per_step
            gantry.move(0, 0, 0.3)
            return True
        else:
            self.calibrate()
        print("Calibration complete.")


gantry = GantryControl(max_x=600, max_y=450)
gantry.initialise()
print(gantry.get_status())

gantry.calibrate()

gantry.move(0, 2, 0.3)
gantry.move(2, 2, 0.3)
gantry.move(2, 0, 0.3)
gantry.move(0, 0, 0.3)

radius = 5  # Define the radius of the circle
angles = np.arange(0, 360, 5)
for angle in angles:
    x = radius * np.cos(np.radians(angle))
    y = radius * np.sin(np.radians(angle))
    gantry.move(x, y, 1.0)
    print(gantry.get_status())
gantry.move(radius * np.cos(np.radians(0)), radius * np.sin(np.radians(0)), 1.0)

# 3.5 girth penis
# x = np.linspace(-3, 3, 100)
# y = (np.abs(np.sin(x)) + 5 * np.exp(-x**100) * np.cos(x))*3.5

# for i in range(len(x)):
#     gantry.move(x[i]*3.5, y[i], 0.1)
#     print(gantry.get_status())


print(gantry.get_status())
gantry.stop()
print(gantry.get_status())
gantry.home()
print(gantry.get_status())
gantry.cleanup()

