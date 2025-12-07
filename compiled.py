import time
import sys
import os
import serial
from gpiozero import RotaryEncoder, Button
from RPLCD.i2c import CharLCD
from gtts import gTTS

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600

# GPIO PINS
PIN_ENCODER_A = 17
PIN_ENCODER_B = 27
PIN_KNOB_BUTTON = 22  # The button inside the rotary knob
PIN_AI_BUTTON = 5     # The separate button for Deep Learning Model

# --- CROP DATABASE ---
CROPS = [
    {
        'name': 'Rice', 
        'hi_name': 'चावल', 
        'n': 60, 'p': 30, 'k': 20, 
        'limit': 250, # Very wet soil required
        'fert_name': 'DAP'
    },
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
        'limit': 350, 
        'fert_name': 'Urea'
    }
]

# --- SETUP HARDWARE ---
try:
    lcd = CharLCD('PCF8574', address=0x27, port=1, cols=16, rows=2)
    lcd.clear()
    print("LCD Initialized")
except Exception as e:
    print(f"LCD Error: {e}")
    sys.exit(1)

# Controls
encoder = RotaryEncoder(a=PIN_ENCODER_A, b=PIN_ENCODER_B, max_steps=0)
knob_button = Button(PIN_KNOB_BUTTON, pull_up=True, bounce_time=0.05)
ai_button = Button(PIN_AI_BUTTON, pull_up=True, bounce_time=0.05)

# Serial Connection
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

# --- CORE FUNCTIONS ---

def speak(text, lang='hi'):
    """Speaks the text using Google TTS and mpg123"""
    print(f"[Voice Output]: {text}")
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        filename = "temp_voice.mp3"
        tts.save(filename)
        os.system(f"mpg123 -q {filename}")
    except Exception as e:
        print(f"TTS Error (Check Internet): {e}")

def get_real_moisture():
    """Reads moisture from Arduino via Serial"""
    global ser
    if not ser:
        return 500 # Default Mock value if sensor missing
    try:
        ser.reset_input_buffer()
        while True: # Blocking read until data found
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

def get_fixed_npk():
    """Returns FIXED NPK values (Low nutrient soil simulation)"""
    return {
        'n': 20, 
        'p': 20, 
        'k': 20
    }

def get_fixed_npk_ph():
    """Returns FIXED data for AI Model"""
    return {
        'n': 20, 
        'p': 20, 
        'k': 20, 
        'ph': 6.5
    }

# --- OPERATION 1: SPECIFIC CROP ANALYSIS (Knob Button) ---

def analyze_specific_crop(crop_idx):
    selected_crop = CROPS[crop_idx]
    hindi_crop = selected_crop['hi_name']
    rec_fertilizer = selected_crop['fert_name'] 
    
    lcd.clear()
    lcd.write_string("Analyzing...")
    
    speak(f"Abhi lagayi gayi fasal hai - {hindi_crop}. Anuman lagaya ja raha hai, kripya prateeksha karein.")
    
    # 1. Get Data
    moisture = get_real_moisture() # REAL SENSOR
    soil_npk = get_fixed_npk()     # FIXED VALUES (20, 20, 20)
    
    print(f"Debug -> Crop: {selected_crop['name']} | Moist: {moisture} | Soil NPK: {soil_npk}")

    # 2. Calculations
    water_needed = 0
    if moisture > selected_crop['limit']:
        diff = moisture - selected_crop['limit']
        water_needed = round(diff * 0.05, 1)

    manure_needed = 0
    if soil_npk['n'] < selected_crop['n']:
        n_diff = selected_crop['n'] - soil_npk['n']
        manure_needed = round(n_diff * 0.05, 1)

    # 3. Result Voice Logic
    voice_msg = ""
    if water_needed == 0 and manure_needed == 0:
        voice_msg = "Mitti ki jaanch safal hui. Abhi kuch daalne ki awashyakta nahi hai aur paani bhi paryapt maatra mein hai."
    else:
        if water_needed > 0:
            voice_msg += f"{water_needed} liter prati varg meter paani daalein. "
        else:
            voice_msg += "Paani paryapt maatra mein hai. "
        
        if manure_needed > 0:
            voice_msg += f"{manure_needed} gram prati varg meter {rec_fertilizer} khaad daalein."
        else:
            voice_msg += "Khaad paryapt maatra mein hai."

    # Display
    lcd.clear()
    lcd.write_string(f"Water: {water_needed}L")
    lcd.crlf()
    lcd.write_string(f"Fert: {manure_needed}g")
    
    speak(voice_msg)
    time.sleep(2)

# --- OPERATION 2: AI CROP RECOMMENDATION (New Button) ---

def run_dl_prediction():
    """
    Simulates a Deep Learning Model.
    Uses FIXED NPK/pH but REAL Moisture.
    """
    lcd.clear()
    lcd.write_string("Running AI Model")
    lcd.crlf()
    lcd.write_string("Please Wait...")
    
    speak("Smart AI Model chalu ho raha hai. Mitti ke tatvon ki jaanch ki ja rahi hai.")
    
    # 1. Gather Data
    data = get_fixed_npk_ph()      # FIXED (20, 20, 20, 6.5)
    moisture = get_real_moisture() # REAL SENSOR
    
    print("--- AI INPUT DATA ---")
    print(f"N: {data['n']} | P: {data['p']} | K: {data['k']} | pH: {data['ph']} | Moist: {moisture}")
    
    # Fake processing delay
    time.sleep(2) 
    
    # 2. AI Logic (Decision Tree)
    prediction = ""
    hindi_prediction = ""
    
    # Logic adjusted for our fixed inputs (N=20)
    if moisture < 250: # If sensor is in water
        prediction = "Rice"
        hindi_prediction = "Chaawal"
    elif data['n'] > 80:
        prediction = "Cotton"
        hindi_prediction = "Kapaas"
    elif data['ph'] < 5.5:
        prediction = "Potato"
        hindi_prediction = "Aaloo"
    elif data['n'] <= 30: # Since our fixed N is 20, this will likely trigger
        prediction = "Legumes"
        hindi_prediction = "Dalhan Fasal"
    else:
        prediction = "Maize"
        hindi_prediction = "Makka"

    # 3. Output
    lcd.clear()
    lcd.write_string("Best Crop:")
    lcd.crlf()
    lcd.write_string(f"> {prediction}")
    
    print(f"[AI RESULT] Best Crop is: {prediction}")
    
    result_msg = f"AI ke anusaar, is mitti ke liye sabse behtar fasal, {hindi_prediction}, rahegi."
    speak(result_msg)
    
    time.sleep(3)


# --- MAIN MENU LOOP ---

def show_menu(idx):
    crop_name = CROPS[idx]['name']
    lcd.clear()
    lcd.write_string("Select Crop:")
    lcd.crlf()
    lcd.write_string(f"> {crop_name}")

current_index = 0
last_pos = 0

# Startup Sequence
print("System Starting...")
speak("Kisaan plus , smart agricultural system activated", lang='en')
show_menu(current_index)

try:
    print("System Running.")
    print("1. Rotate Knob to select crop.")
    print("2. Press Knob Button (GPIO 22) to analyze specific crop.")
    print("3. Press AI Button (GPIO 5) to predict BEST crop.")
    
    while True:
        # 1. Rotary Encoder Logic (Menu Scroll)
        pos = encoder.steps
        if pos != last_pos:
            diff = pos - last_pos
            current_index = (current_index + diff) % len(CROPS)
            last_pos = pos
            show_menu(current_index)

        # 2. Check Knob Button (Specific Analysis)
        if knob_button.is_pressed:
            time.sleep(0.1) # Debounce
            if knob_button.is_pressed:
                analyze_specific_crop(current_index)
                show_menu(current_index)
                last_pos = encoder.steps
        
        # 3. Check AI Button (Deep Learning Prediction)
        if ai_button.is_pressed:
            time.sleep(0.1) # Debounce
            if ai_button.is_pressed:
                run_dl_prediction()
                show_menu(current_index)
        
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    lcd.clear()
    lcd.close(clear=True)
    if ser:
        ser.close()
