import time
import sys
import os
import random
import serial
from gpiozero import RotaryEncoder, Button
from RPLCD.i2c import CharLCD
from gtts import gTTS

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600

# We use a LIST [ ] so the Rotary Encoder can scroll through them easily.
CROPS = [
    {
        'name': 'Tomato', 
        'hi_name': 'टमाटर', 
        'n': 22, 'p': 35, 'k': 45, 
        'limit': 300, 
        'fert_name': 'NPK 10-20-20' 
    },
    {
        'name': 'Lettuce', 
        'hi_name': 'सलाद पत्ता', 
        'n': 18, 'p': 25, 'k': 30, 
        'limit': 250, 
        'fert_name': 'NPK 15-15-15'
    },
    {
        'name': 'Carrot', 
        'hi_name': 'गाजर', 
        'n': 15, 'p': 30, 'k': 40, 
        'limit': 350, 
        'fert_name': 'NPK 5-15-15'
    },
    {
        'name': 'Potato', 
        'hi_name': 'आलू', 
        'n': 25, 'p': 45, 'k': 50, 
        'limit': 400, 
        'fert_name': 'NPK 8-24-24'
    },
    {
        'name': 'Wheat', 
        'hi_name': 'गेहूँ', 
        'n': 50, 'p': 30, 'k': 20, 
        'limit': 400, 
        'fert_name': 'Urea'
    }
]

# --- SETUP ---
try:
    lcd = CharLCD('PCF8574', address=0x27, port=1, cols=16, rows=2)
    lcd.clear()
    print("LCD Initialized")
except Exception as e:
    print(f"LCD Error: {e}")
    sys.exit(1)

encoder = RotaryEncoder(a=17, b=27, max_steps=0)
button = Button(22, pull_up=True, bounce_time=0.05)

ser = None
try:
    print(f"Connecting to {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.reset_input_buffer()
    time.sleep(2)
    print("Serial Connected!")
except Exception as e:
    print(f"Serial Error: {e}")
    print("Proceeding with Mock Data for testing...")

# --- FUNCTIONS ---

def speak(text, lang='hi'):
    print(f"[Voice Output]: {text}")
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        filename = "temp_voice.mp3"
        tts.save(filename)
        os.system(f"mpg123 -q {filename}")
    except Exception as e:
        print(f"TTS Error (Check Internet): {e}")

def get_real_moisture():
    global ser
    # Debug prints removed for cleaner console, but logic remains Blocking
    if not ser:
        return random.randint(200, 600)
    
    try:
        ser.reset_input_buffer()
        while True:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line.isdigit():
                        return int(line)
                except:
                    pass
            time.sleep(0.1)
    except:
        return 400

def get_mock_npk():
    return {
        'n': random.randint(10, 60),
        'p': random.randint(10, 60),
        'k': random.randint(10, 60)
    }

def show_menu(idx):
    crop_name = CROPS[idx]['name']
    lcd.clear()
    lcd.write_string("Select Crop:")
    lcd.crlf()
    lcd.write_string(f"> {crop_name}")

def analyze_and_report(crop_idx):
    selected_crop = CROPS[crop_idx]
    hindi_crop = selected_crop['hi_name']
    rec_fertilizer = selected_crop['fert_name'] # Get the specific fertilizer name
    
    lcd.clear()
    lcd.write_string("Analyzing...")
    
    # 1. Start Analysis Message
    speak(f"Abhi lagayi gayi fasal hai - {hindi_crop}. Anuman lagaya ja raha hai, kripya prateeksha karein.")
    
    # 2. Get Data
    moisture = get_real_moisture()
    soil_npk = get_mock_npk()
    print(f"Debug -> Crop: {selected_crop['name']} | Moist: {moisture}")

    # 3. Calculations
    water_needed = 0
    if moisture > selected_crop['limit']:
        diff = moisture - selected_crop['limit']
        water_needed = round(diff * 0.05, 1)

    manure_needed = 0
    if soil_npk['n'] < selected_crop['n']:
        n_diff = selected_crop['n'] - soil_npk['n']
        manure_needed = round(n_diff * 0.05, 1)

    # 4. Result Logic
    voice_msg = ""
    
    if water_needed == 0 and manure_needed == 0:
        voice_msg = "Mitti ki jaanch safal hui. Abhi kuch daalne ki awashyakta nahi hai aur paani bhi paryapt maatra mein hai."
    else:
        # Water Result
        if water_needed > 0:
            voice_msg += f"{water_needed} liter paani daalein. "
        else:
            voice_msg += "Paani paryapt maatra mein hai. "
        
        # Fertilizer Result (Using specific name now)
        if manure_needed > 0:
            voice_msg += f"{manure_needed} gram prati varg meter {rec_fertilizer} khaad daalein."
        else:
            voice_msg += "Khaad paryapt maatra mein hai."

    # Display Result
    lcd.clear()
    lcd.write_string(f"Water: {water_needed}L")
    lcd.crlf()
    lcd.write_string(f"Fert: {manure_needed}g") # Changed to 'g' for grams logic
    
    speak(voice_msg)
    
    time.sleep(2)

# --- MAIN LOOP ---

current_index = 0
last_pos = 0

# 1. Startup Message (English)
print("System Starting...")
speak("Kisaan plus , smart agricultural system activated", lang='en')

show_menu(current_index)

try:
    print("System Running. Press Ctrl+C to exit.")
    while True:
        pos = encoder.steps
        if pos != last_pos:
            diff = pos - last_pos
            current_index = (current_index + diff) % len(CROPS)
            last_pos = pos
            show_menu(current_index)

        if button.is_pressed:
            time.sleep(0.1)
            if button.is_pressed:
                analyze_and_report(current_index)
                show_menu(current_index)
                last_pos = encoder.steps
        
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    lcd.clear()
    lcd.close(clear=True)
    if ser:
        ser.close()
