import time
from djitellopy import tello
from threading import Thread
import keyboard
from logger import Logger

class MinimalSubscriber():

    def __init__(self):
        # Initialize logger and command state
        self.log = Logger("log1.csv")
        self.command = "stand"
        self.keyboard_thread = Thread(target=self.keyboard_control)
        self.log_thread = Thread(target=self.log_update)

        # Connect to the Drone
        self.me = tello.Tello()
        self.me.connect()   

        # Print the Battery percentage
        print("Battery percentage:", self.me.get_battery())
        
        if self.me.get_battery() < 10:
            raise RuntimeError("Tello rejected attempt to takeoff due to low Battery")

        self.current_altitude = 0  # Track the current altitude
        self.initial_yaw = None    # Initial yaw to be set on takeoff
        self.yaw_target = 0        # Target yaw angle
        self.keyboard_thread.start()

    def keyboard_control(self):
        """
        This method allows the user to control the drone using the keyboard.
        """
        tookoff = False
        yaw_speed = 60  # Yaw speed, you can adjust this value
        yaw_step = 60   # Yaw step in degrees for each key press

        while True:
            if keyboard.is_pressed('esc'):
                print("Exiting program.")
                if tookoff:
                    self.me.land()
                break

            # Takeoff / Land
            if keyboard.is_pressed('space'):
                if not tookoff:
                    self.me.takeoff()
                    tookoff = True
                    self.command = "takeoff"
                    self.initial_yaw = self.me.get_yaw()  # Set initial yaw on takeoff
                    self.yaw_target = self.initial_yaw
                else:
                    self.me.land()
                    tookoff = False
                    self.command = "land"

            # Emergency
            if keyboard.is_pressed('e'):
                try:
                    print("EMERGENCY")
                    self.me.emergency()
                except Exception as e:
                    print("Did not receive OK, reconnecting to Tello")
                    self.me.connect()

            # Altitude Control
            if keyboard.is_pressed('up'):
                self.current_altitude += 20  # Increase altitude by 20 cm
                self.command = "UP"
                self.move_to_height(self.current_altitude)
            
            if keyboard.is_pressed("down"):
                self.current_altitude -= 20  # Decrease altitude by 20 cm
                self.command = "DOWN"
                self.move_to_height(self.current_altitude)

            # Yaw Control
            if keyboard.is_pressed('a'):
                self.yaw_target -= yaw_step  # Rotate left by yaw_step degrees
                self.command = "YAW LEFT"
                self.rotate_to_yaw(self.yaw_target)

            if keyboard.is_pressed('d'):
                self.yaw_target += yaw_step  # Rotate right by yaw_step degrees
                self.command = "YAW RIGHT"
                self.rotate_to_yaw(self.yaw_target)

            # Send the command to the drone
            self.me.send_rc_control(0, 0, 0, 0)

    def move_to_height(self, target_height):
        """
        Moves the drone to the target height.
        """
        current_height = self.me.get_height()
        if target_height > current_height:
            while current_height < target_height:
                self.me.send_rc_control(0, 0, 50, 0)  # Move upward
                time.sleep(0.1)
                current_height = self.me.get_height()
        elif target_height < current_height:
            while current_height > target_height:
                self.me.send_rc_control(0, 0, -50, 0)  # Move downward
                time.sleep(0.1)
                current_height = self.me.get_height()
        self.me.send_rc_control(0, 0, 0, 0)  # Stop movement
        print(f"Reached desired height: {target_height} cm")

    def rotate_to_yaw(self, target_yaw):
        """
        Rotates the drone to the target yaw angle.
        """
        current_yaw = self.me.get_yaw()
        yaw_speed = 50  # Adjust yaw speed if needed

        # Normalize target_yaw to be within [0, 360)
        target_yaw = target_yaw % 360

        while abs(current_yaw - target_yaw) > 1:  # Small tolerance for reaching exact yaw
            current_yaw = self.me.get_yaw()
            if (target_yaw - current_yaw + 360) % 360 <= 180:
                self.me.send_rc_control(0, 0, 0, yaw_speed)
            else:
                self.me.send_rc_control(0, 0, 0, -yaw_speed)
            time.sleep(0.1)

        self.me.send_rc_control(0, 0, 0, 0)  # Stop rotation
        print(f"Reached target yaw: {target_yaw} degrees")

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
