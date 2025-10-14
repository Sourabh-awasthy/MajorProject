# Smart Soil Analyzer for Raspberry Pi 4
# This script reads soil data, allows crop selection via a knob,
# and provides fertilizer recommendations on an OLED display.

import time
import random

# --- Hardware Abstraction Layer ---
# This section contains mock functions and classes to simulate hardware.
# On your Raspberry Pi, you would replace the code in this section
# with the actual libraries for your specific hardware components.
# For example, for an SSD1306 OLED, you'd use the 'adafruit_ssd1306' library.
# For GPIO, you'd use 'RPi.GPIO' or 'gpiozero'.

class MockOLED:
    """A mock class to simulate an OLED display. It prints to the console."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        print(f"--- Mock OLED Initialized ({width}x{height}) ---")

    def fill(self, color):
        """Simulates clearing the display."""
        # In a real scenario, this would clear the display buffer.
        pass

    def text(self, text, x, y, color):
        """Simulates drawing text on the display."""
        print(f"[OLED DISPLAY] at ({x},{y}): {text}")

    def show(self):
        """Simulates updating the display with the buffer content."""
        print("------------------------------------")
        # On real hardware, this pushes the buffer to the screen.
        time.sleep(1) # Simulate the time it takes to update the screen

def read_soil_sensor():
    """
    MOCK FUNCTION: Simulates reading data from a soil sensor.
    Replace this with your sensor's actual reading function.
    This should return a dictionary with nutrient values.
    """
    # These values would come from your I2C/SPI/Analog sensor
    sensor_data = {
        'nitrogen': round(random.uniform(5, 25), 1),  # in mg/kg
        'phosphorus': round(random.uniform(10, 40), 1), # in mg/kg
        'potassium': round(random.uniform(15, 55), 1)  # in mg/kg
    }
    print(f"[SENSOR READ]: {sensor_data}")
    return sensor_data

# --- Configuration and Data ---

# Pre-fed data for different crops.
# In a real-world application, this could be loaded from a file (e.g., JSON or CSV).
CROP_DATA = {
    'Rice': {
        'nitrogen': 22.0, 'phosphorus': 35.0, 'potassium': 45.0,
        'recommendation_fertilizer': 'NPK 10-20-20'
    },
    'Wheat': {
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

# Conversion factor to translate nutrient deficiency (in mg/kg) to
# fertilizer quantity (in gm/sq. m). This is a simplified value.
# (Deficiency * FACTOR) = gm/sq. m. You may need to adjust this.
NUTRIENT_TO_FERTILIZER_FACTOR = 0.5

# --- Main Application Logic ---

class SoilAnalyzerApp:
    def __init__(self):
        # Initialize hardware
        # For a 128x64 OLED display
        self.oled = MockOLED(128, 64)

        # Application state
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
        """
        MOCK FUNCTION: Simulates user input from the knob and button.
        In your actual code, this would check GPIO pins.
        """
        # We use command-line input to simulate hardware interaction
        print("\n--- WAITING FOR INPUT ---")
        print("Enter 'k+' (knob clockwise), 'k-' (knob counter-clockwise),")
        print("or 'b' (compute button press), 'q' (quit):")
        choice = input("> ").lower()
        self.last_knob_input = ''
        self.last_button_input = ''

        if choice == 'k+':
            self.last_knob_input = 'clockwise'
        elif choice == 'k-':
            self.last_knob_input = 'counter-clockwise'
        elif choice == 'b':
            self.last_button_input = 'pressed'
        elif choice == 'q':
            self.running = False


    def compute_recommendation(self):
        """The core logic that is triggered by the button press."""
        selected_crop_name = self.crops[self.current_crop_index]
        ideal_levels = CROP_DATA[selected_crop_name]
        fertilizer_type = ideal_levels['recommendation_fertilizer']

        self.update_display("Analyzing...", "Reading sensors...")
        current_levels = read_soil_sensor()

        # Calculate deficiencies
        n_diff = ideal_levels['nitrogen'] - current_levels['nitrogen']
        p_diff = ideal_levels['phosphorus'] - current_levels['phosphorus']
        k_diff = ideal_levels['potassium'] - current_levels['potassium']

        # Find the most deficient nutrient to make a single recommendation
        deficiencies = {'Nitrogen': n_diff, 'Phosphorus': p_diff, 'Potassium': k_diff}
        most_deficient_nutrient = max(deficiencies, key=deficiencies.get)
        max_deficiency = deficiencies[most_deficient_nutrient]

        if max_deficiency > 2.0: # Only recommend if deficiency is significant
            amount_to_add = round(max_deficiency * NUTRIENT_TO_FERTILIZER_FACTOR, 1)
            line1 = "Recommendation:"
            line2 = f"Add {amount_to_add} gm/sq.m"
            line3 = f"of {fertilizer_type}"
            line4 = f"for {most_deficient_nutrient}"
        else:
            line1 = "Soil is healthy!"
            line2 = "No fertilizer"
            line3 = "needed for"
            line4 = selected_crop_name

        self.update_display(line1, line2, line3, line4)
        time.sleep(5) # Show the message for 5 seconds before returning to crop selection

    def run(self):
        """The main loop of the application."""
        print("Starting Smart Soil Analyzer...")
        # Initial display
        self.update_display("Select Crop:", self.crops[self.current_crop_index], "Press 'b' to compute")

        while self.running:
            self.get_user_input()

            # Handle knob input
            if self.last_knob_input == 'clockwise':
                self.current_crop_index = (self.current_crop_index + 1) % len(self.crops)
            elif self.last_knob_input == 'counter-clockwise':
                self.current_crop_index = (self.current_crop_index - 1 + len(self.crops)) % len(self.crops)

            # Handle button press
            if self.last_button_input == 'pressed':
                self.compute_recommendation()

            # Update display after any action
            self.update_display("Select Crop:", self.crops[self.current_crop_index], "Press 'b' to compute")

        print("Shutting down.")


if __name__ == "__main__":
    app = SoilAnalyzerApp()
    app.run()
