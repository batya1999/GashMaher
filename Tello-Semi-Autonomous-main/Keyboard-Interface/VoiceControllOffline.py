import time
from djitellopy import tello
from threading import Thread
from logger import Logger
import speech_recognition as sr
import keyboard

class MinimalSubscriber:
    def __init__(self):
        # Initialize PID parameters
        self.kp = 0.8  # Proportional gain
        self.ki = 0.1  # Integral gain
        self.kd = 0.05  # Derivative gain
        self.previous_error = 0
        self.integral = 0

        # Initialize logger and command state
        self.log = Logger("log1.csv")
        self.command = "stand"
        self.initial_yaw = None  # Variable to store the initial yaw
        self.drone_flying = False

        # Connect to the Drone
        self.me = tello.Tello()
        self.me.connect()

        # Print the Battery percentage
        print("Battery percentage:", self.me.get_battery())
        if self.me.get_battery() < 10:
            raise RuntimeError("Tello rejected attempt to takeoff due to low battery")

        # Start the voice command listening thread
        self.speech_thread = Thread(target=self.listen_for_commands, daemon=True)
        self.speech_thread.start()

        # Start keyboard monitoring thread
        self.keyboard_thread = Thread(target=self.keyboard_control, daemon=True)
        self.keyboard_thread.start()

        # Keep the main thread alive to keep the program running
        self.keep_running()

    def listen_for_commands(self):
        """
        Listens for voice commands to start the flight sequence and land the drone.
        """
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)

            print("Say 'up' to start the flight sequence. Say 'down' to land the drone. Press 'esc' to exit the program.")

            while True:
                if keyboard.is_pressed('esc'):
                    print("Exiting program.")
                    if self.me.get_flying():
                        self.me.land()  # Ensure drone lands if exiting
                    break

                try:
                    print("Listening for commands...")
                    audio = recognizer.listen(source, timeout=5)
                    command = recognizer.recognize_sphinx(audio).lower()
                    print(f"You said: {command}")
                    first_letter = command[0]
                    
                    if command == "up" or first_letter in ('a', 'u', 'o', 'b'):
                        if not self.drone_flying:
                            print("Starting flight sequence...")
                            self.takeoff_and_execute_sequence()
                    
                    elif command == "down" or first_letter == 'd':
                        if self.drone_flying:
                            print("Landing...")
                            self.me.land()
                            self.drone_flying = False

                except sr.UnknownValueError:
                    print("Sorry, I did not understand that.")
                except sr.RequestError:
                    print("Sorry, there was an error with the speech recognition service.")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

    def takeoff_and_execute_sequence(self):
        """
        Takes off, ascends to 1 meter, rotates 90 degrees to the right, rotates back to the initial yaw,
        and waits for the 'down' command to land.
        """
        # Takeoff
        self.me.takeoff()
        print("Taking off...")
        time.sleep(1)

        # Store the initial yaw angle
        if self.initial_yaw is None:
            self.initial_yaw = self.me.get_yaw()

        # Rotate 90 degrees to the right
        self.rotate_to_yaw_pid(self.initial_yaw + 90)

        # Rotate back to the initial yaw
        self.rotate_to_yaw_pid(self.initial_yaw)

        # Set drone flying flag
        self.drone_flying = True
        print("Drone is flying. Say 'down' to land the drone.")

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
            print(f"Yaw speed: {yaw_speed}")

            # Apply the control
            self.me.send_rc_control(0, 0, 0, int(yaw_speed))

            time.sleep(0.1)
            if keyboard.is_pressed('esc'):
                print("Emergency: Landing now.")
                self.me.land()
                self.drone_flying = False
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
                self.drone_flying = False
                break
            time.sleep(0.1)

    def keep_running(self):
        """
        Keep the main thread alive to ensure background threads continue running.
        """
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Program interrupted by user.")
            if self.me.get_flying():
                self.me.land()  # Ensure drone lands if exiting
            self.log_update()

    def log_update(self):
        """   
        Update the state of the drone into the log file.
        """
        while True:
            state = self.me.get_current_state()
            if len(state) == 21:
                self.log.add(state, self.command, 0)

if __name__ == '__main__':
    MinimalSubscriber()
