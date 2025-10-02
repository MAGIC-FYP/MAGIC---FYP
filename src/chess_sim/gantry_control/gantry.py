import numpy as np
import lgpio
import time



class GantryControl:
    def __init__(self, max_x: float, min_x: float, max_y: float, min_y: float, motor_radius: float = 0.95):
        # Pin definitions (using BCM numbering)
        self.L_DIR = 9   # Direction
        self.L_STEP = 8  # Step pulse
        self.R_DIR = 11   # Direction
        self.R_STEP = 10  # Step pulse

        self.E_MAG = 12 
        self.LED = 13

        self.x_sw = 14
        self.y_sw = 15
        
        # Initialize GPIO handles to None
        self.lg = None  # Main GPIO handle
        
        # Motor control parameters
        self.start_delay = 0.003   # 3ms (gentle start)
        self.end_delay = 0.0001    # 1.5ms (gentle max speed)
        self.pulse_width = 0.003 # 30us
        
        self.x_offest = 2.2
        self.y_offest = -1.52

        # Physical parameters
        self.max_x = max_x                  # in cm
        self.max_y = max_y                  # in cm
        self.x_pos = self.x_offest          # in cm
        self.x_vel = 0                      # in cm/s
        self.y_pos = self.y_offest          # in cm
        self.y_vel = 0                      # in cm/s
        self.l_motor_pos = 0                # in rads
        self.l_motor_vel = 0                # in rads/s
        self.r_motor_pos = 0                # in rads
        self.r_motor_vel = 0                # in rads/s

        self.motor_radius = motor_radius    # in cm
        self.M = np.array([[1,0],[0,-1]])
        
        # Steps per revolution (typical for stepper motors)
        self.cm_per_step = 0.008


    def initialise(self):
        # Setup
        self.lg = lgpio.gpiochip_open(0)
        #stepper pins
        lgpio.gpio_claim_output(self.lg, self.L_DIR)
        lgpio.gpio_claim_output(self.lg, self.L_STEP)
        lgpio.gpio_claim_output(self.lg, self.R_DIR)
        lgpio.gpio_claim_output(self.lg, self.R_STEP)

        #electromagnet pins
        lgpio.gpio_claim_output(self.lg, self.E_MAG)
        #led pin
        lgpio.gpio_claim_output(self.lg, self.LED)

        lgpio.gpio_claim_input(self.lg, self.x_sw)
        lgpio.gpio_claim_input(self.lg, self.y_sw)

        # Initialize pins low
        lgpio.gpio_write(self.lg, self.L_STEP, 0)
        lgpio.gpio_write(self.lg, self.L_DIR, 0)
        lgpio.gpio_write(self.lg, self.R_STEP, 0)
        lgpio.gpio_write(self.lg, self.R_DIR, 0)
        lgpio.gpio_write(self.lg, self.E_MAG, 0)
        lgpio.gpio_write(self.lg, self.LED, 0)

        print(f"lg: {self.lg}")
        print("Pins initialized")
        return True
    def s_curve_delays(self,start_delay, end_delay, steps):
        """
        Generate an S-curve (smoothstep) delay profile for acceleration/deceleration.
        Returns a list of delays (in seconds) for each step.
        """
        if steps <= 0:
            return []
        t = np.linspace(0, 1, steps)
        s = 3 * t**2 - 2 * t**3  # Smoothstep S-curve
        return (start_delay + (end_delay - start_delay) * s).tolist()

    def electromagnet(self, on: bool):
        lgpio.gpio_write(self.lg, self.E_MAG, 1 if on else 0)
        lgpio.gpio_write(self.lg, self.LED, 1 if on else 0)
        return True


    def move_steps(self, direction_left, direction_right, num_steps_left, num_steps_right, start_delay=None, end_delay=None, pulse_width=None, monitor=False):
        """Move stepper motor with acceleration/deceleration ramps"""
        if start_delay is None:
            start_delay = self.start_delay
        if end_delay is None:
            end_delay = self.end_delay
        if pulse_width is None:
            pulse_width = self.pulse_width
            
        lgpio.gpio_write(self.lg, self.L_DIR, direction_left)
        lgpio.gpio_write(self.lg, self.R_DIR, direction_right)
        
        steps_left = abs(num_steps_left)
        steps_right = abs(num_steps_right)
        max_steps = max(steps_left, steps_right)
        ramp_steps = min(20, max_steps // 2)  # 20 steps or half the move, whichever is less
        const_steps = max_steps - 2 * ramp_steps

        delays = (
            self.s_curve_delays(start_delay, end_delay, ramp_steps) +
            [end_delay] * max(0, const_steps) +
            self.s_curve_delays(end_delay, start_delay, ramp_steps)
        )
        # Bresenham error for sync stepping
        error = 0
        left_counter = 0
        right_counter = 0
        for i in range(max_steps):
            step_left = False
            step_right = False
            if steps_left >= steps_right:
                step_left = True
                error += steps_right
                if error * 2 >= steps_left:
                    step_right = True
                    error -= steps_left
            else:
                step_right = True
                error += steps_left
                if error * 2 >= steps_right:
                    step_left = True
                    error -= steps_right
            
            if step_left and left_counter < steps_left:
                lgpio.gpio_write(self.lg, self.L_STEP, 1)
                time.sleep(pulse_width)
                lgpio.gpio_write(self.lg, self.L_STEP, 0)
                left_counter += 1
                self.x_pos -= 0.5*((direction_left*2)-1)*self.cm_per_step
                self.y_pos -= 0.5*((direction_left*2)-1)*self.cm_per_step
            if step_right and right_counter < steps_right:
                lgpio.gpio_write(self.lg, self.R_STEP, 1)
                time.sleep(pulse_width)
                lgpio.gpio_write(self.lg, self.R_STEP, 0)
                right_counter += 1
                self.x_pos += 0.5*((direction_right*2)-1)*self.cm_per_step
                self.y_pos -= 0.5*((direction_right*2)-1)*self.cm_per_step
            
            # Shared delay for both motors
            if monitor:
                sw_state = (lgpio.gpio_read(self.lg, self.x_sw)+(lgpio.gpio_read(self.lg, self.y_sw)*2))
                if (sw_state) != 0:
                    if sw_state == 1:
                        self.x_pos = self.x_offest
                        self.move_steps(0,1,10,10)
                    elif sw_state == 2:
                        self.y_pos = self.y_offest
                        self.move_steps(0,0,10,10)
                    elif sw_state == 3:
                        self.x_pos = self.x_offest
                        self.y_pos = self.y_offest
                        self.move_steps(0,1,10,10)
                        self.move_steps(0,0,10,10)
                    print(f"switch hit, Sw state: {sw_state}")
                    return False
            
            #print(f"x_pos: {self.x_pos}, y_pos: {self.y_pos}")
            time.sleep(delays[i] if i < len(delays) else end_delay)
            
            
            # Update position tracking
            step_distance_left = self.cm_per_step * (1 if direction_left == 1 else -1)
            step_distance_right = self.cm_per_step * (1 if direction_right == 1 else -1)
            # This is a simplified update - in reality you'd need to track both motors
            # self.x_pos += step_distance_left * 0.5  # Assuming equal contribution from both motors
            # self.y_pos += step_distance_right * 0.5

    

        return True

    def move(self, x: float, y: float, vel: float):
        """Move to target position with specified velocity"""
        x = -x  # Flip the x-axis
        if not (x < self.max_x or x > self.min_x):
            raise ValueError("Target position out of bounds")
        if not (y < self.max_y or y > self.min_y):
            raise ValueError("Target position out of bounds")
        
        delta_x = -x - self.x_pos
        delta_y = -y + self.y_pos
        print(f"Delta x: {delta_x}, Delta y: {delta_y}")
        distance = np.sqrt((delta_x**2) + (delta_y**2))
        #print(f"Distance: {distance}, Delta x: {delta_x}, Delta y: {delta_y}")
        
        if distance < 0.1:  # Already at target
            return

        left_steps = int(abs(delta_x-delta_y) / self.cm_per_step)
        right_steps = int(abs(-delta_x-delta_y) / self.cm_per_step)

        # Determine directions
        left_dir = 1 if  -delta_x+delta_y> 0 else 0
        right_dir = 1 if  delta_x+delta_y> 0 else 0
        
        
        if vel <= 0:
            calculated_pulse_width = self.pulse_width
        else:
            calculated_pulse_width = self.cm_per_step / (2 * vel)
        
        # Clamp the calculated pulse_width within the defined min/max limits
        pulse_width = calculated_pulse_width
        
        #print(f"Moving to ({x:.2f}, {y:.2f}) - Left: {left_steps} steps, Right: {right_steps} steps")
        
        # Move both motors (simplified - in reality you'd need to coordinate them)
        if left_steps+right_steps > 0:
            while True:
                if self.move_steps(left_dir, right_dir, left_steps, right_steps, pulse_width=pulse_width, monitor=True):
                    break
                else:
                    time.sleep(0.8)
                    
                    self.move(-x, y, vel)
                    self.x_pos = -x
                    self.y_pos = y
                    return True
        
            
        # Update final position
        self.x_pos = -x
        self.y_pos = y
        return True
    
    def move_reletive(self, x: float, y: float, vel: float):
        x_abs = self.x_pos + x
        y_abs = self.y_pos + y
        print(f"Moving to ({x_abs}, {y_abs})")
        self.move(x_abs, y_abs, vel)
        return True
    

    def home(self):
        fast_home_speed = 0.0005
        while lgpio.gpio_read(self.lg, self.x_sw) == 0:
            self.move_steps(1,0,1,1, pulse_width=fast_home_speed)
        self.move_steps(0,1,100,100, pulse_width=fast_home_speed)
        while lgpio.gpio_read(self.lg, self.x_sw) == 0:
            self.move_steps(1,0,1,1)
        self.move_steps(0,1,20,20)
        print("Homed X")

        """Home the gantry to origin"""
        print("Homing to origin...")
        while lgpio.gpio_read(self.lg, self.y_sw) == 0:
            self.move_steps(1,1,1,1, pulse_width=fast_home_speed)
        self.move_steps(0,0,100,100, pulse_width=fast_home_speed)
        while lgpio.gpio_read(self.lg, self.y_sw) == 0:
            self.move_steps(1,1,1,1)
        self.move_steps(0,0,20,20)
        print("Homed Y")
    
        self.x_pos = self.x_offest
        self.y_pos = self.y_offest
        print("Homing complete.")
        return True

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
        lgpio.gpiochip_close(self.lg)
        print("GPIO cleanup complete.")


    def test_stepper(self):
        lgpio.gpio_write(self.lg, self.R_STEP, 1)
        time.sleep(self.pulse_width)
        lgpio.gpio_write(self.lg, self.R_STEP, 0)
        for i in range(100):
            lgpio.gpio_write(self.lg, self.R_STEP, 1)
            time.sleep(self.pulse_width)
            lgpio.gpio_write(self.lg, self.R_STEP, 0)
            time.sleep(0.005)

        for i in range(100):
            lgpio.gpio_write(self.lg, self.L_STEP, 1)
            time.sleep(self.pulse_width)
            lgpio.gpio_write(self.lg, self.L_STEP, 0)
            time.sleep(0.005)

    def test_square(self, length=2):
        self.move(0, length, 0.3)
        self.move(length, length, 0.3)
        self.move(length, 0, 0.3)
        self.move(0, 0, 0.3)
        return True
    def draw_pawn(self):
        pawn_outline = [
            (0, 0),    # base left
            (20, 0),   # base right
            (18, 5),
            (15, 10),
            (12, 20),
            (10, 30),
            (9, 40),
            (10, 50),  # bottom of head
            (12, 55),  # top of head
            (8, 55),   # left head arc
            (10, 50),
            (9, 40),
            (8, 30),
            (6, 20),
            (3, 10),
            (0, 5),
            (0, 0)     # close the shape
        ]
        for point in pawn_outline:
            self.move(point[0]*0.5, point[1]*0.5, 1.0)
        return True
    
    def test_axis(self):
        self.move(2, 0, 4)
        self.move(0, 0, 4)
        self.move(0, 2, 4)
        self.move(0, 0, 4)
        return True
            
    def test_constantcy(self, length=2):
        self.move(2, 25, 0.3)
        self.move(32, 25, 0.3)
        self.move(32, 23, 0.3)
        self.move(2, 23, 0.3)
        self.move(2, 21, 0.3)
        self.move(32, 21, 0.3)
        self.move(32, 19, 0.3)
        self.move(2, 19, 0.3)
        self.move(2, 17, 0.3)
        self.move(32, 17, 0.3)
        self.move(32, 15, 0.3)
        self.move(2, 15, 0.3)
        radius = 5  # Define the radius of the circle
        angles = np.arange(0, 360, 10)  # or even 0.5 for ultra-smooth
        for i in range(2):
            for angle in angles:
                x = radius * np.cos(np.radians(angle))
                y = radius * np.sin(np.radians(angle))
                self.move(x+15, y+15, 1.0)
                print(self.get_status())
            self.move((radius * np.cos(np.radians(0)))+15, (radius * np.sin(np.radians(0)))+15, 1.0)
        self.move(2, 0, 0.3)
        self.move(32, 0, 0.3)
        self.move(32, 2, 0.3)
        self.move(2, 2, 0.3)
        self.move(2, 4, 0.3)
        self.move(32, 4, 0.3)
        self.move(32, 2, 0.3)
        self.move(2, 2, 0.3)
        self.move(2, 0, 0.3)
        self.move(32, 0, 0.3)
        self.move(32, 2, 0.3)
        self.home()
        return True
    
    def draw_cool_dimond(self):
        speed = 1
        points = [
            (10, 0),
            (0, 0),
            (0, 1),
            (10, 0),
            (9, 0),
            (0, 2),
            (0, 3),
            (8, 0),
            (7, 0),
            (0, 4),
            (0, 5),
            (6, 0),
            (5, 0),
            (0, 6),
            (0, 7),
            (4, 0),
            (3, 0),
            (0, 8),
            (0, 9),
            (2, 0),
            (1, 0),
            (0, 10),
            (0, 0)
        ]
        for point in points:
            self.move(point[0], point[1], speed)
        for point in points:
            self.move(-point[0], point[1], speed)
        for point in points:
            self.move(-point[0], -point[1], speed)
        for point in points:
            self.move(point[0], -point[1], speed)
        return True
    
    def draw_circle(self,x_offset=0, y_offset=0, radius=5, speed=1):
        angles = np.arange(0, 360, 10)  # or even 0.5 for ultra-smooth
        for angle in angles:
            x = radius * np.cos(np.radians(angle))
            y = radius * np.sin(np.radians(angle))
            self.move(x+x_offset, y+y_offset, speed)
            self.home()
        self.move(x_offset+radius * np.cos(np.radians(0)), y_offset+radius * np.sin(np.radians(0)), speed)
        return

    def draw_cool_circle(self,x_offset=0, y_offset=0, step=9, outer_radius=10, num_points=40, speed=1):
        angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        x = x_offset + outer_radius * np.cos(angles)
        y = y_offset + outer_radius * np.sin(angles)
        vertices = np.stack((x, y), axis=1)

        # Create the star path by connecting every 'step'-th point
        indices = [(i * step) % num_points for i in range(num_points + 1)]
        star_points = vertices[indices]
        for point in star_points:
            self.move(point[0], point[1], speed)

        self.move(0, 0, speed)  # Close the shape
        return True
    
    def chime(self):
        dist = 0.5
        speed = 50
        if self.x_pos > (self.max_x-1):
            self.move_reletive(-dist, -dist, 50)
            time.sleep(0.15)
            self.move_reletive(dist, dist, 50)
        
        else:
            self.move_reletive(dist, dist, 50)
            time.sleep(0.15)
            self.move_reletive(-dist, -dist, 50)
        
        
        return True
    
    def calibrate(self):
        """Calibrate the gantry"""
        print("Calibrating gantry...")
        self.move(0, 0, 1)
        pulse_width = 0.003
        for i in range(500):
            lgpio.gpio_write(self.lg, self.R_STEP, 1)

            time.sleep(pulse_width)
            lgpio.gpio_write(self.lg, self.R_STEP, 0)
            time.sleep(pulse_width)

        
        cm = float(input("Enter cm to moved: "))
        cm_per_step = ((cm*np.sqrt(2)) / (500))
        self.x_pos += -cm/np.sqrt(2)
        self.y_pos += -cm/np.sqrt(2)
        print(f"x_pos: {self.x_pos}, y_pos: {self.y_pos}")
        
        print(f"cm_per_step: {self.cm_per_step}")
        self.move(0,cm*2/np.sqrt(2),1)
        print(f"x_pos: {self.x_pos}, y_pos: {self.y_pos}")
        yN = input(f"is this {cm}cm y/n? ")
        if yN == "y":
            self.cm_per_step = cm_per_step
            gantry.move(0, 0, 1)
            return True
        else:
            self.calibrate()
        print("Calibration complete.")


# gantry = GantryControl(max_x=36, min_x=1.75, max_y=32, min_y=-1.6)
# gantry.initialise()
# gantry.chime()
# print(gantry.get_status())

#gantry.test_axis()
#gantry.calibrate()
#gantry.test_square(length=2)
#gantry.test_constantcy()
#gantry.draw_cool_dimond()
# radius = 5  # Define the radius of the circle
# angles = np.arange(0, 360, 10)  # or even 0.5 for ultra-smooth
# for angle in angles:
#     x = radius * np.cos(np.radians(angle))
#     y = radius * np.sin(np.radians(angle))
#     gantry.move(x, y, 1.0)
#     gantry.home()
#     print(gantry.get_status())
# gantry.move(radius * np.cos(np.radians(0)), radius * np.sin(np.radians(0)), 1.0)
# gantry.electromagnet(True)
# gantry.move(5,5,2)

#gantry.home()
# gantry.move_reletive(5,5,20)
# gantry.chime()
# gantry.move_reletive(10,10,10)
# gantry.move_reletive(10,0,20)
# gantry.move_reletive(-10,0,30)
# gantry.move_reletive(10,0,35)
# gantry.move_reletive(-10,0,40)
# # time.sleep(3)
# #gantry.move(0,0,1)
# # gantry.move(-10,5,1)
# #lgpio.gpio_write(gantry.lg, gantry.E_MAG, 1)

# while True:
#     input("Press keyborad turn on mag")
#     gantry.electromagnet(True)

#     gantry.move_reletive(10,0,5)
#     input("Press keyborad turn off mag")
#     gantry.electromagnet(False)
#     gantry.move_reletive(-10,0,5)

    
# gantry.cleanup()

