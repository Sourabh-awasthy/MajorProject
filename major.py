# Smart Soil Analyzer for Raspberry Pi 4
# This script reads soil data, allows crop selection via a knob,
# and provides fertilizer recommendations on an OLED display and via voice in Hindi.

import time
import random
import os
from gtts import gTTS

# --- Hardware Abstraction Layer ---
# This section contains mock functions and classes to simulate hardware.
# On your Raspberry Pi, you would replace the code in this section
# with the actual libraries for your specific hardware components.

class MockOLED:
    """A mock class to simulate an OLED display. It prints to the console."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        print(f"--- Mock OLED Initialized ({width}x{height}) ---")

    def fill(self, color):
        """Simulates clearing the display."""
        pass

    def text(self, text, x, y, color):
        """Simulates drawing text on the display."""
        print(f"[OLED DISPLAY] at ({x},{y}): {text}")

    def show(self):
        """Simulates updating the display with the buffer content."""
        print("------------------------------------")
        time.sleep(1)

def read_soil_sensor():
    """MOCK FUNCTION: Simulates reading data from a soil sensor."""
    sensor_data = {
        'nitrogen': round(random.uniform(5, 25), 1),
        'phosphorus': round(random.uniform(10, 40), 1),
        'potassium': round(random.uniform(15, 55), 1)
    }
    print(f"[SENSOR READ]: {sensor_data}")
    return sensor_data

# --- New Function for Voice Output ---
def speak_hindi(text_to_speak):
    """
    Converts text to speech in Hindi and plays the audio.
    Requires an internet connection to work.
    """
    try:
        print(f"[VOICE OUTPUT] Speaking: '{text_to_speak}'")
        # Create gTTS object
        tts = gTTS(text=text_to_speak, lang='hi')
        # Save the audio file
        audio_file = "recommendation.mp3"
        tts.save(audio_file)
        # Play the audio file using mpg123
        os.system(f"mpg123 -q {audio_file}")
    except Exception as e:
        print(f"An error occurred during text-to-speech: {e}")
        print("Please ensure you are connected to the internet and have mpg123 installed.")

# --- Configuration and Data ---

CROP_DATA = {
    'Tomato': {
        'nitrogen': 22.0, 'phosphorus': 35.0, 'potassium': 45.0,
        'recommendation_fertilizer': 'NPK 10-20-20'
    },
    'Lettuce': {
        'nitrogen': 18.0, 'phosphorus': 25.0, 'potassium': 30.0,
        'recommendation_fertilizer': 'Balanced NPK 15-15-15'
    },
    'Carrot': {
        'nitrogen': 15.0, 'phosphorus': 30.0, 'potassium': 40.0,
        'recommendation_fertilizer': 'Low-N NPK 5-15-15'
    },
    'Potato': {
        'nitrogen': 25.0, 'phosphorus': 45.0, 'potassium': 50.0,
        'recommendation_fertilizer': 'High-P/K NPK 8-24-24'
    }
}

NUTRIENT_TO_FERTILIZER_FACTOR = 0.5

# --- Main Application Logic ---

class SoilAnalyzerApp:
    def __init__(self):
        self.oled = MockOLED(128, 64)
        self.crops = list(CROP_DATA.keys())
        self.current_crop_index = 0
        self.running = True
        self.last_knob_input = ''
        self.last_button_input = ''

    def update_display(self, line1, line2="", line3="", line4=""):
        """Clears the OLED and displays up to four lines of text."""
        self.oled.fill(0)
        self.oled.text(line1, 0, 0, 1)
        self.oled.text(line2, 0, 15, 1)
        self.oled.text(line3, 0, 30, 1)
        self.oled.text(line4, 0, 45, 1)
        self.oled.show()

    def get_user_input(self):
        """MOCK FUNCTION: Simulates user input from the knob and button."""
        print("\n--- WAITING FOR INPUT ---")
        print("Enter 'k+' (knob clockwise), 'k-' (knob counter-clockwise),")
        print("or 'b' (compute button press), 'q' (quit):")
        choice = input("> ").lower()
        self.last_knob_input = ''
        self.last_button_input = ''
        if choice == 'k+': self.last_knob_input = 'clockwise'
        elif choice == 'k-': self.last_knob_input = 'counter-clockwise'
        elif choice == 'b': self.last_button_input = 'pressed'
        elif choice == 'q': self.running = False

    def compute_recommendation(self):
        """The core logic that is triggered by the button press."""
        selected_crop_name = self.crops[self.current_crop_index]
        ideal_levels = CROP_DATA[selected_crop_name]
        fertilizer_type = ideal_levels['recommendation_fertilizer']

        self.update_display("Analyzing...", "Reading sensors...")
        speak_hindi("Anumaan lagaya ja raha hai. Kripya pratiksha karein.")
        current_levels = read_soil_sensor()

        n_diff = ideal_levels['nitrogen'] - current_levels['nitrogen']
        p_diff = ideal_levels['phosphorus'] - current_levels['phosphorus']
        k_diff = ideal_levels['potassium'] - current_levels['potassium']

        deficiencies = {'Nitrogen': n_diff, 'Phosphorus': p_diff, 'Potassium': k_diff}
        most_deficient_nutrient = max(deficiencies, key=deficiencies.get)
        max_deficiency = deficiencies[most_deficient_nutrient]

        display_text = []
        speech_text = ""

        if max_deficiency > 2.0:
            amount_to_add = round(max_deficiency * NUTRIENT_TO_FERTILIZER_FACTOR, 1)
            display_text = [
                "Recommendation:",
                f"Add {amount_to_add} gm/sq.m",
                f"of {fertilizer_type}",
                f"for {most_deficient_nutrient}"
            ]
            speech_text = f"{most_deficient_nutrient} ke liye, {amount_to_add} gram prati varg meter {fertilizer_type} khaad daalein."
        else:
            display_text = [
                "Soil is healthy!",
                "No fertilizer",
                "needed for",
                selected_crop_name
            ]
            speech_text = f"{selected_crop_name} ke liye mitti swasth hai. Khaad ki avashyakta nahi hai."

        self.update_display(*display_text)
        speak_hindi(speech_text)

        time.sleep(3) # Wait before returning to the main screen

    def run(self):
        """The main loop of the application."""
        print("Starting Smart Soil Analyzer...")
        speak_hindi("Smart Soil Analyzer shuru ho gaya hai.")
        
        while self.running:
            self.update_display("Select Crop:", self.crops[self.current_crop_index], "Press 'b' to compute")
            self.get_user_input()

            if self.last_knob_input == 'clockwise':
                self.current_crop_index = (self.current_crop_index + 1) % len(self.crops)
            elif self.last_knob_input == 'counter-clockwise':
                self.current_crop_index = (self.current_crop_index - 1 + len(self.crops)) % len(self.crops)

            if self.last_button_input == 'pressed':
                self.compute_recommendation()
        
        speak_hindi("Application band ho raha hai.")
        print("Shutting down.")

if __name__ == "__main__":
    app = SoilAnalyzerApp()
    app.run()
