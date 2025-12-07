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

CROPS = [
    {'name': 'Wheat',  'hi_name': 'गेहूँ',   'n': 50, 'p': 30, 'k': 20, 'limit': 400},
    {'name': 'Rice',   'hi_name': 'चावल',   'n': 60, 'p': 30, 'k': 20, 'limit': 250},
    {'name': 'Maize',  'hi_name': 'मक्का',   'n': 80, 'p': 40, 'k': 30, 'limit': 350},
    {'name': 'Cotton', 'hi_name': 'कपास',   'n': 70, 'p': 30, 'k': 40, 'limit': 450},
    {'name': 'Tomato', 'hi_name': 'टमाटर',  'n': 22, 'p': 35, 'k': 45, 'limit': 300},
]

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

def speak(text):
    print(f"[Voice Output]: {text}")
    try:
        tts = gTTS(text=text, lang='hi', slow=False)
        filename = "temp_voice.mp3"
        tts.save(filename)
        os.system(f"mpg123 {filename}")
    except Exception as e:
        print(f"TTS Error (Check Internet): {e}")

def get_real_moisture():
    global ser
    if not ser:
        return random.randint(300, 600)
    
    try:
        ser.reset_input_buffer()
        
        for _ in range(10):
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').rstrip()
                if line.isdigit():
                    return int(line)
        return 400
    except Exception as e:
        print(f"Read Error: {e}")
        return 400

def get_mock_npk():
    return {
        'n': random.randint(10, 90),
        'p': random.randint(10, 90),
        'k': random.randint(10, 90)
    }

def show_menu(idx):
    crop_name = CROPS[idx]['name']
    lcd.clear()
    lcd.write_string("Select Crop:")
    lcd.crlf()
    lcd.write_string(f"> {crop_name}")

def analyze_and_report(crop_idx):
    selected_crop = CROPS[crop_idx]
    
    lcd.clear()
    lcd.write_string("Analyzing...")
    
    moisture = get_real_moisture()
    soil_npk = get_mock_npk()
    print(f"Debug -> Crop: {selected_crop['name']} | Moist: {moisture}")

    water_needed = 0
    if moisture > selected_crop['limit']:
        diff = moisture - selected_crop['limit']
        water_needed = round(diff * 0.05, 1)

    manure_needed = 0
    if soil_npk['n'] < selected_crop['n']:
        n_diff = selected_crop['n'] - soil_npk['n']
        manure_needed = round(n_diff * 0.05, 1)

    hindi_crop = selected_crop['hi_name']
    voice_msg = f"{hindi_crop} के लिए परिणाम। "
    
    if water_needed == 0 and manure_needed == 0:
        voice_msg += "मिट्टी पूरी तरह से स्वस्थ है।"
    else:
        if water_needed > 0:
            voice_msg += f"{water_needed} लीटर पानी डालें। "
        if manure_needed > 0:
            voice_msg += f"{manure_needed} किलो खाद डालें।"

    lcd.clear()
    lcd.write_string(f"Water: {water_needed}L")
    lcd.crlf()
    lcd.write_string(f"Manure: {manure_needed}Kg")
    
    speak(voice_msg)
    
    time.sleep(2)

current_index = 0
last_pos = 0

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
