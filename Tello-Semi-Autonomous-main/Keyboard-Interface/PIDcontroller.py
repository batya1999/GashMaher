import time
from djitellopy import tello
from threading import Thread
from logger import Logger
import keyboard  

class MinimalSubscriber:

    def __init__(self):

        self.kp = 0.8  # Proportional gain
        self.ki = 0.1 # Integral gain
        self.kd = 0.05  # Derivative gain
        self.previous_error = 0
        self.integral = 0

        # Initialize logger and command state
        self.log = Logger("log1.csv")
        self.command = "stand"
        self.initial_yaw = None  # Variable to store the initial yaw

        # Connect to the Drone
        self.me = tello.Tello()
        self.me.connect()

        # Print the Battery percentage
        print("Battery percentage:", self.me.get_battery())

        if self.me.get_battery() < 10:
            raise RuntimeError("Tello rejected attempt to takeoff due to low battery")

        # Start the sequence
        self.takeoff_and_execute_sequence()

        # Start keyboard monitoring thread
        self.keyboard_thread = Thread(target=self.keyboard_control)
        self.keyboard_thread.start()

    def takeoff_and_execute_sequence(self):
        """
        Takes off, ascends to 1 meter, rotates 90 degrees to the right, rotates back to the initial yaw,
        hovers for 2 seconds, and then lands.
        """
        # Takeoff
        self.me.takeoff()
        print("Taking off...")
        time.sleep(0.1)

        # Store the initial yaw angle
        if self.initial_yaw is None:
            self.initial_yaw = self.me.get_yaw()

        # Rotate 90 degrees to the right
        self.rotate_to_yaw_pid(self.initial_yaw + 90)

        # Rotate back to the initial yaw
        self.rotate_to_yaw_pid(self.initial_yaw)

        # Hover for 2 seconds
        print("Hovering...")
        time.sleep(2)  # Hover for 2 seconds

        # Land the drone
        print("Landing...")
        self.me.land()
        self.command = "landed"
        print("Landed successfully.")

    def rotate_to_yaw_pid(self, target_yaw):
        """
        Rotates the drone to the target yaw angle using a PID controller.
        """
        current_yaw = self.me.get_yaw()
        previous_time = time.time()
        time.sleep(0.1)

        while abs(current_yaw - target_yaw) > 1:  # Small tolerance for reaching exact yaw
            current_yaw = self.me.get_yaw()

            # Calculate error
            error = target_yaw - current_yaw

            # Calculate the time difference
            current_time = time.time()
            delta_time = current_time - previous_time
            previous_time = current_time

            # Proportional term
            p_term = self.kp * error

            # Integral term
            self.integral += error * delta_time    
            i_term = self.ki * self.integral

            # Derivative term
            derivative = (error - self.previous_error) / delta_time
            d_term = self.kd * derivative
            self.previous_error = error

            # Calculate the control variable (yaw speed)
            yaw_speed = p_term + i_term + d_term

            # Clamp yaw speed to a safe range (optional)
            max_yaw_speed = 500  # You can adjust this limit
            yaw_speed = max(-max_yaw_speed, min(yaw_speed, max_yaw_speed))
            print(yaw_speed)

            # Apply the control
            self.me.send_rc_control(0, 0, 0, int(yaw_speed))

            time.sleep(0.1)
            if keyboard.is_pressed('esc'):
                print("Emergency: Landing now.")
                self.me.land()
                break

        self.me.send_rc_control(0, 0, 0, 0)  # Stop rotation
        print(f"Reached target yaw: {target_yaw} degrees")

    def keyboard_control(self):
        """
        Monitor keyboard input to control the drone and handle emergency landing.
        """
        while True:
            if keyboard.is_pressed('esc'):
                print("Emergency: Landing now.")
                self.me.land()
                break
            time.sleep(0.1)

    def log_update(self):
        """   
        Update the state of the drone into the log file.
        """
        while True:
            state = self.me.get_current_state()
            if len(state) == 21:
                self.log.add(state, self.command, 0)

if __name__ == '__main__':
    tello = MinimalSubscriber()
