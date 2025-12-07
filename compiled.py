import time
import sys
import os
import random
import serial
from gpiozero import RotaryEncoder, Button
from RPLCD.i2c import CharLCD

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyUSB0' # Change to /dev/ttyACM0 if needed
BAUD_RATE = 9600

# Crop Database
# 'limit': The moisture value above which the soil is considered DRY.
CROPS = [
    {'name': 'Wheat',   'n': 50, 'p': 30, 'k': 20, 'limit': 400},
    {'name': 'Rice',    'n': 60, 'p': 30, 'k': 20, 'limit': 250},
    {'name': 'Maize',   'n': 80, 'p': 40, 'k': 30, 'limit': 350},
    {'name': 'Cotton',  'n': 70, 'p': 30, 'k': 40, 'limit': 450},
    {'name': 'Tomato',  'n': 22, 'p': 35, 'k': 45, 'limit': 300},
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
    """Text-to-Speech using espeak-ng"""
    print(f"[Voice]: {text}")
    # -s 160 is speed
    os.system(f'espeak-ng -s 160 "{text}" --stdout | aplay -q')

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
    """Main Logic: Reads data -> Calculates -> Speaks"""
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

    # 3. Create Voice Message
    msg = f"Result for {selected_crop['name']} per square meter. "
    
    if water_needed == 0 and manure_needed == 0:
        msg += "Soil is healthy."
    else:
        if water_needed > 0:
            msg += f"Add {water_needed} liters of water. "
        if manure_needed > 0:
            msg += f"Add {manure_needed} kilos of manure."

    # 4. Display & Speak
    
    # Show Water
    lcd.clear()
    lcd.write_string(f"Water: {water_needed}L")
    lcd.crlf()
    lcd.write_string(f"Manure: {manure_needed}Kg")
    
    speak(msg)
    
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
