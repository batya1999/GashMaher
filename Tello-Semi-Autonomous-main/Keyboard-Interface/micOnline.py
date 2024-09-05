import speech_recognition as sr
import keyboard
import sys

def listen_for_commands():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening... Press 'esc' to exit or say 'exit' to stop.")

        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)
        
        while True:
            try:
                print("Say something...")
                audio = recognizer.listen(source)

                # Recognize speech using Google Web Speech API
                command = recognizer.recognize_google(audio).lower()
                print(f"You said: {command}")

                if command == "up":
                    print("Up")
                elif command == "down":
                    print("Down")
                elif command == "left":
                    print("Left")
                elif command == "right":
                    print("Right")
                elif command == "exit":
                    print("Exiting...")
                    break
                else:
                    print("Command not recognized.")
                
            except sr.UnknownValueError:
                print("Sorry, I did not understand that.")
            except sr.RequestError:
                print("Sorry, there was an error with the speech recognition service.")

            # Check if 'esc' key is pressed to exit
            if keyboard.is_pressed('esc'):
                print("Esc key pressed. Exiting...")
                break

if __name__ == "__main__":
    try:
        listen_for_commands()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
        sys.exit(0)
