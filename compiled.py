import time
import sys
import os
import random
import serial
from gpiozero import RotaryEncoder, Button
from RPLCD.i2c import CharLCD
from gtts import gTTS  # Added gTTS

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyUSB0' # Change to /dev/ttyACM0 if needed
BAUD_RATE = 9600

# Crop Database
# Added 'hi_name' for Hindi Voice output
CROPS = [
    {'name': 'Wheat',  'hi_name': 'गेहूँ',   'n': 50, 'p': 30, 'k': 20, 'limit': 400},
    {'name': 'Rice',   'hi_name': 'चावल',   'n': 60, 'p': 30, 'k': 20, 'limit': 250},
    {'name': 'Maize',  'hi_name': 'मक्का',   'n': 80, 'p': 40, 'k': 30, 'limit': 350},
    {'name': 'Cotton', 'hi_name': 'कपास',   'n': 70, 'p': 30, 'k': 40, 'limit': 450},
    {'name': 'Tomato', 'hi_name': 'टमाटर',  'n': 22, 'p': 35, 'k': 45, 'limit': 300},
]

# --- HARDWARE SETUP ---

# 1. Setup LCD (16x2)
try:
    # Address might be 0x27 or 0x3F. Using your proven 0x27.
    lcd = CharLCD('PCF8574', address=0x27, port=1, cols=16, rows=2)
    lcd.clear()
    print("LCD Initialized")
except Exception as e:
    print(f"LCD Error: {e}")
    sys.exit(1)

# 2. Setup Controls
encoder = RotaryEncoder(a=17, b=27, max_steps=0)
button = Button(22, pull_up=True, bounce_time=0.05)

# 3. Setup Serial (Your Verified Code Logic)
ser = None
try:
    print(f"Connecting to {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.reset_input_buffer()
    time.sleep(2) # Wait for Nano/Sensor to reset
    print("Serial Connected!")
except Exception as e:
    print(f"Serial Error: {e}")
    print("Proceeding with Mock Data for testing...")

# --- FUNCTIONS ---

def speak(text):
    """Text-to-Speech using Google TTS (Hindi) and mpg321"""
    print(f"[Voice Output]: {text}")
    try:
        # Generate MP3 using Google API
        # lang='hi' ensures it speaks in Hindi
        tts = gTTS(text=text, lang='hi', slow=False)
        filename = "temp_voice.mp3"
        tts.save(filename)
        
        # Play the file using mpg321
        os.system(f"mpg321 {filename}")
        
        # Optional: remove file after playing to save space
        # os.remove(filename) 
    except Exception as e:
        print(f"TTS Error (Check Internet): {e}")

def get_real_moisture():
    """Reads sensor using your exact logic"""
    global ser
    if not ser:
        return random.randint(300, 600) # Mock if hardware missing
    
    try:
        ser.reset_input_buffer() # Clear old buffer to get FRESH reading
        
        # Read a few lines to skip potential partial lines
        for _ in range(10):
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').rstrip()
                if line.isdigit():
                    return int(line)
        return 400 # Default if read fails
    except Exception as e:
        print(f"Read Error: {e}")
        return 400

def get_mock_npk():
    """Generates random NPK values (since we don't have NPK sensors)"""
    return {
        'n': random.randint(10, 90),
        'p': random.randint(10, 90),
        'k': random.randint(10, 90)
    }

def show_menu(idx):
    """Updates LCD with current selection"""
    crop_name = CROPS[idx]['name']
    lcd.clear()
    lcd.write_string("Select Crop:")
    lcd.crlf()
    lcd.write_string(f"> {crop_name}")

def analyze_and_report(crop_idx):
    """Main Logic: Reads data -> Calculates -> Speaks (in Hindi)"""
    selected_crop = CROPS[crop_idx]
    
    # User Feedback
    lcd.clear()
    lcd.write_string("Analyzing...")
    
    # 1. Get Data
    moisture = get_real_moisture()
    soil_npk = get_mock_npk()
    print(f"Debug -> Crop: {selected_crop['name']} | Moist: {moisture}")

    # 2. Logic
    # Water Calculation
    water_needed = 0
    if moisture > selected_crop['limit']:
        diff = moisture - selected_crop['limit']
        water_needed = round(diff * 0.05, 1)

    # Manure Calculation
    manure_needed = 0
    if soil_npk['n'] < selected_crop['n']:
        n_diff = selected_crop['n'] - soil_npk['n']
        manure_needed = round(n_diff * 0.05, 1)

    # 3. Create Voice Message (IN HINDI)
    # We construct a Hindi string here for gTTS
    
    hindi_crop = selected_crop['hi_name']
    voice_msg = f"{hindi_crop} के लिए परिणाम। "
    
    if water_needed == 0 and manure_needed == 0:
        voice_msg += "मिट्टी पूरी तरह से स्वस्थ है।"
    else:
        if water_needed > 0:
            # Translating: "Add X liters water" -> "X liter paani daalein"
            voice_msg += f"{water_needed} लीटर पानी डालें। "
        if manure_needed > 0:
            # Translating: "Add Y kg manure" -> "Y kilo khaad daalein"
            voice_msg += f"{manure_needed} किलो खाद डालें।"

    # 4. Display & Speak
    
    # Show Water on LCD (In English for display compatibility)
    lcd.clear()
    lcd.write_string(f"Water: {water_needed}L")
    lcd.crlf()
    lcd.write_string(f"Manure: {manure_needed}Kg")
    
    # Speak the Hindi message
    speak(voice_msg)
    
    # Pause so user can read before menu returns
    time.sleep(2)

# --- MAIN LOOP ---

current_index = 0
last_pos = 0

show_menu(current_index)

try:
    print("System Running. Press Ctrl+C to exit.")
    while True:
        # 1. Rotary Logic
        pos = encoder.steps
        if pos != last_pos:
            diff = pos - last_pos
            # Update index with wrapping
            current_index = (current_index + diff) % len(CROPS)
            last_pos = pos
            show_menu(current_index)

        # 2. Button Logic
        if button.is_pressed:
            time.sleep(0.1) # Debounce
            if button.is_pressed:
                analyze_and_report(current_index)
                
                # Reset Menu
                show_menu(current_index)
                # Sync encoder position to avoid jumps
                last_pos = encoder.steps
        
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    lcd.clear()
    lcd.close(clear=True)
    if ser:
        ser.close()
