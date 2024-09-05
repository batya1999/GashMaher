import speech_recognition as sr
import keyboard
import time

def listen_for_commands():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)
        
        print("Press 'space' to start listening. Press 'esc' to exit the program.")
        
        listening = False

        while True:
            if keyboard.is_pressed('space'):
                if not listening:
                    print("Listening...")
                    listening = True
                
                while listening:
                    try:
                        print("Say something...")
                        audio = recognizer.listen(source)

                        # Recognize speech using Sphinx
                        command = recognizer.recognize_sphinx(audio).lower()
                        print(f"You said: {command}")

                        # Determine the action based on the starting letter
                        if command:
                            first_letter = command[0]
                            if first_letter in ('a', 'u', 'o', 'b'):
                                print("Up")
                            elif first_letter == 'd':
                                print("Down")
                            elif first_letter == 'l':
                                print("Left")
                            elif first_letter == 'r':
                                print("Right")
                            else:
                                print("Command not recognized.")
                        
                        if command == "exit":
                            print("Exiting...")
                            listening = False
                            break  # Exit the listening loop
                    
                    except sr.UnknownValueError:
                        print("Sorry, I did not understand that.")
                    except sr.RequestError:
                        print("Sorry, there was an error with the speech recognition service.")
                    
                    # Check if 'esc' key is pressed to exit listening mode
                    if keyboard.is_pressed('esc'):
                        print("Esc key pressed. Exiting...")
                        return  # Exit the main loop
            
            # Check if 'esc' key is pressed to exit the program
            if keyboard.is_pressed('esc'):
                print("Exiting program.")
                return  # Exit the program

            time.sleep(0.1)  # To prevent excessive CPU usage

if __name__ == "__main__":
    try:
        listen_for_commands()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
 