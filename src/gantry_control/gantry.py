import numpy as np
import time

class GantryControl:
    def __init__(self, max_x: float, max_y: float, motor_radius: float):

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

    def initialise(self):
        #TODO: some initilaisation
        pass

    def move(self, x: float, y: float, vel: float):
        if not (x<self.max_x and y<self.max_y):
            raise ValueError("Target position out of bounds")
        
        delta_x = x - self.x_pos
        delta_y = y - self.y_pos
        angle = np.arctan2(delta_y, delta_x)
        a = vel * np.cos(angle)
        b = vel * np.sin(angle)
        d_dot = np.array([[a-b], [-a-b]])
        w_dot = (1/self.motor_radius)*self.M*d_dot
        t = np.sqrt((delta_x**2)+(delta_y**2))/vel
    

        start_time = time.time()

        #TODO: use actual motor movemnt command
        self.l_motor_vel = w_dot[0]
        self.r_motor_vel = w_dot[1]

        while time.time() < start_time + t:
            time.sleep(0.01)
            elapsed = time.time() - start_time
            progress = min(elapsed/t, 1.0)
            self.x_pos = self.x_pos + delta_x * progress
            self.y_pos = self.y_pos + delta_y * progress
            self.l_motor_pos = self.l_motor_pos + w_dot[0] * progress * elapsed
            self.r_motor_pos = self.r_motor_pos + w_dot[1] * progress * elapsed

        self.stop()
        self.x_pos = x
        self.y_pos = y
        
    def stop(self):
        #TODO: use actual motor movemnt command
        self.l_motor_vel = 0 
        self.r_motor_vel = 0

    def home(self):
        #TODO: some homing function or what to find where it is if it gets lost
        pass

    def get_status(self):
        #TODO: use encoder posses instead of self posses
        return {
            "x_pos": self.x_pos,
            "y_pos": self.y_pos,
            "l_motor_pos": self.l_motor_pos,
            "r_motor_pos": self.r_motor_pos,
            "l_motor_vel": self.l_motor_vel,
            "r_motor_vel": self.r_motor_vel
        }

