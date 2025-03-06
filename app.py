
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import requests
import pyautogui
import subprocess
from flask_cors import CORS
import threading
import time
import uuid
import csv
import secrets
import psutil
import ctypes
import datetime
import pvporcupine
import pyaudio
import textwrap
import struct
import screen_brightness_control as sbc
from youtubesearchpython import VideosSearch
import pygetwindow as gw
import google.generativeai as genai
from dotenv import load_dotenv
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pywinauto import Application
from picovoice import Picovoice
from pvrecorder import PvRecorder  # Correct imp
from pvporcupine import Porcupine


cooldown_seconds = 1.0
last_wake_time = 0
wake_lock = threading.Lock()

ACCESS_KEY = "WaP34juT5J7Gppb6YJS1e4SNACzHyo93kOKOgnOIuOr7Uq3u/o0nzw=="

app = Flask (__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = '4f3c7d8c91a94e2ebd4a3f97a02f4bc1db927aaef7a66b7c1e0f2c5c3d8b0e27'
# Initialize TTS engine inside function to avoid conflicts
# Add global flag
is_speaking = False

# Modified speak function
def speak(text):
    global is_responding, tts_engine, is_speaking
    is_responding = True
    is_speaking = True  # 🔴 New flag
    
    try:
        engine = pyttsx3.init("sapi5")
        tts_engine = engine
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[1].id)
        
        for chunk in text.split('. '):
            if not is_responding:
                break
            engine.say(chunk.strip())
            engine.runAndWait()
    finally:
        tts_engine = None
        is_speaking = False  # 🔴 Reset flag

# Global conversation history
latest_command = None
conversation_history = []
CITY = "kakinada"
API_KEY = "aab6a0497bdb1b1a69a06274739c0d4a"

is_wake_handled = False  # 🔴 NEW: Track wake word handling
is_responding = True     # 🔴 NEW: Track response state
processing_lock = threading.Lock()  # 🔴 NEW: Prevent concurrent processing
last_wake_time = 0
WAKE_COOLDOWN = 2  # 2 seconds cooldown
tts_engine = None
cooldown_seconds=2
is_listening = False
wake_lock = threading.Lock()

# Set paths for your offline model and keyword file (use your actual model path here)
wake_word_model_path = [r"C:\Users\siva sandeep penkey\OneDrive\Apps\Desktop\Nyra\nyra\hey-sam_en_windows_v3_0_0\hey-sam_en_windows_v3_0_0.ppn"]  # Replace with actual path to .ppn file
library_path = r"C:\Users\siva sandeep penkey\OneDrive\Apps\Desktop\Nyra\nyra\porcupine-master\porcupine-master\lib\windows\amd64\libpv_porcupine.dll"
 # Correct path to the library
sensitivities = [0.5]  # Sensitivity for the wake word detection (0.0 to 1.0)
ACCESS_KEY = "UlN9KkcCLhS+3z7O3xDjsdbdtOxf8AlzL9YjaAKWK1SaNUBK8VZ9sw=="
# Initialize the recorder
recorder = PvRecorder(device_index=-1, frame_length=512)  # Adjust according to your setup



load_dotenv()
# Get API key from .env file
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Error: Gemini API key not found. Please check your .env file.")



# Add at the top with other globals
is_wake_processing = False  # 🔴 New flag for wake word handling

def wake_word_detected():
    global last_wake_time
    current_time = time.time()

    if current_time - last_wake_time < cooldown_seconds:  
        return
        
    with wake_lock:
        last_wake_time = time.time()
        print("Wake word detected! Listening for command...")

        # 🔥 Faster transition to command processing
        def response_flow():
            speak("How can I help you?")
            command = listen()  # Listen without delay
            print(f"Recognized Command: {command}")  # Debugging
            if command:
                process_command(command)

        threading.Thread(target=response_flow, daemon=True).start()



def listen_for_command():
    global is_listening
    if is_listening:
        print("Already listening, ignoring duplicate call...")
        return  # Prevent duplicate executions

    is_listening = True
    print("Listening...")
    # Your existing speech recognition logic here
    time.sleep(3)  # Simulating speech recognition delay
    is_listening = False  # Reset after completion


def handle_command_after_wake():
    command = listen()
    if command:
        process_command(command)

# Initialize Porcupine with your wake word model
porcupine = Porcupine(
    library_path=library_path,  # Path to the dynamic library (e.g., .dll for Windows)
    access_key=ACCESS_KEY,
    model_path=r"C:\Users\siva sandeep penkey\OneDrive\Apps\Desktop\Nyra\nyra\porcupine_params.pv",
    keyword_paths=wake_word_model_path,  # Path to your .ppn wake word model
    sensitivities=sensitivities  # List of sensitivities for the wake word detection
)
audio_stream = pyaudio.PyAudio().open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)

def ask_gemini(query, lines=None):
    """Query Gemini AI with reliable error handling"""
    try:
        # Initialize model with proper configuration
        model = genai.GenerativeModel("gemini-1.5-pro-latest")

        
        # Generate response with safety settings
        response = model.generate_content(
            query,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=200,
                temperature=0.7
            )
        )
        
        # Process response
        if not response or not response.text:
            return "I couldn't process that request. Please try again."
            
        result = response.text.strip()
        
        # Word limit enforcement
        words = result.split()
        if len(words) > 40:
            words = words[:40]
            # Find natural truncation point
            truncated = ' '.join(words)
            last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
            result = truncated[:last_punct+1] if last_punct > 0 else truncated + "..."
        
        # Line wrapping
        if lines:
            result = "\n".join(textwrap.wrap(result, width=80)[:lines])
            
        return result
        
    except Exception as e:
        print(f"API Error: {str(e)}")  # Debug logging
        return "I'm having trouble with that request. Please try again."

def update_conversation(user, response):
    """Appends the conversation history with user input and AI response."""
    conversation_history.append({"user": user, "response": response})

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.energy_threshold = 3000
        recognizer.pause_threshold = 1.5
        
        try:
            audio = recognizer.listen(
                source, 
                timeout=3, 
                phrase_time_limit=5
            )
            return recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            print("Couldn't understand audio")
            return None
        except sr.WaitTimeoutError:
            print("Listening timeout")
            return None
        finally:
            recognizer.dynamic_energy_threshold = True

def start_wake_word_listening():
    """Continuous listening for wake word with faster response"""
    recorder = PvRecorder(device_index=-1, frame_length=512)
    recorder.start()
    
    print("Listening for wake word 'Hey Sam'...")
    try:
        while True:
            if is_speaking:
                time.sleep(0.05)  # 🔥 Reduced wait time
                continue

            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                # Faster Buffer Clearing (Reduce Unnecessary Delay)
                for _ in range(int(16000 * 0.5 // 512)):  # 0.5s buffer
                    recorder.read()
                
                wake_word_detected()
                time.sleep(0.5)  # 🔥 Reduced Cooldown
    finally:
        recorder.stop()
        recorder.delete()

def process_command(command):
    """Process the command given by the user"""
    global latest_command, is_responding
    is_responding = True  # Reset response state for new command
    latest_command = command.lower().strip()
    response = ""
    
    try:
        # Early exit check
        if not is_responding:
            return "Response stopped"
        with processing_lock:  # 🔴 Use processing lock
            is_responding = True
        # Basic commands
        if "open youtube" in command:
            if not is_responding: return "Response stopped"
            webbrowser.open("https://www.youtube.com")
            response = "Opening YouTube."
            
        elif "open google" in command:
            if not is_responding: return "Response stopped"
            webbrowser.open("https://www.google.com")
            response = "Opening Google."
            
        elif "open" in command:
            if not is_responding: return "Response stopped"
            app_name = command.replace("open", "").strip().lower()
            response = open_application(app_name)
        
        # Media controls
        elif "play" in command and "on youtube music" in command:
            if not is_responding: return "Response stopped"
            search_query = command.replace("play", "").replace("on youtube music", "").strip()
            response = play_youtube_music(search_query)
        
        # System status
        elif "what is my battery percentage" in command:
            if not is_responding: return "Response stopped"
            response = get_battery_status()
            
        elif "what is my volume level" in command:
            if not is_responding: return "Response stopped"
            response = get_volume_status()
            
        elif "what is my brightness level" in command:
            if not is_responding: return "Response stopped"
            response = get_brightness_status()

        # Adjustments
        elif any(key in command for key in ["increase volume", "decrease volume", "mute"]):
            if not is_responding: return "Response stopped"
            adjust_volume(command)
            response = "Volume adjusted."
            
        elif any(key in command for key in ["increase brightness", "decrease brightness"]):
            if not is_responding: return "Response stopped"
            adjust_brightness(command)
            response = "Brightness adjusted."

        # YouTube
        elif "play" in command and "on youtube" in command:
            if not is_responding: return "Response stopped"
            search_query = command.replace("play", "").replace("on youtube", "").strip()
            response = play_on_youtube(search_query)

        # System controls
        elif "shutdown laptop" in command:
            if not is_responding: return "Response stopped"
            os.system("shutdown /s /t 1")
            response = "Shutting down laptop."
            
        elif "restart laptop" in command:
            if not is_responding: return "Response stopped"
            os.system("shutdown /r /t 1")
            response = "Restarting laptop."

        elif "sleep laptop" in command or "put laptop to sleep" in command:
            if not is_responding: return "Response stopped"
            try:
                # Add confirmation before sleeping
                speak("Putting laptop to sleep in 2 seconds")
                time.sleep(2)
                ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
                response = ""
            except Exception as e:
                response = f"Failed to sleep: {str(e)}. Need admin rights?"

        # Weather
        elif any(key in command for key in ["weather today", "weather", "temperature"]):
            if not is_responding: return "Response stopped"
            response = get_weather()

        # Time/date
        elif any(key in command for key in ["what is the date", "what is the time", "what is the day"]):
            if not is_responding: return "Response stopped"
            response = get_date_time()

        # UI actions
        elif "is there any notifications" in command:
            if not is_responding: return "Response stopped"
            response = open_notifications()
            
        elif any(key in command for key in ["minimize window", "minimize the window"]):
            if not is_responding: return "Response stopped"
            response = window_action("minimize")
            
        elif any(key in command for key in ["maximize window", "maximize the window"]):
            if not is_responding: return "Response stopped"
            response = window_action("maximize")
            
        elif any(key in command for key in ["close window", "close the window"]):
            if not is_responding: return "Response stopped"
            response = window_action("close")

        # Special UI elements
        elif any(key in command for key in ["launch search", "launch calendar", "launch start"]):
            if not is_responding: return "Response stopped"
            response = open_ui_element(command)

        # AI fallback
        else:
            if not is_responding: return "Response stopped"
            response = ask_gemini(command)
            
    except Exception as e:
        response = f"Error processing command: {str(e)}"
    
    # Final output handling
    if is_responding:
        speak(response)
    else:
        response = "Response stopped"
    
    update_conversation(latest_command, response)
    print(response, flush=True)
    time.sleep(0.5)  # Reduced sleep for better responsiveness
    
    return response

def open_ui_element(command):
    actions = {
        "launch search": (660, 1053),
        "launch calendar": (1833, 1053),
        "launch start": (576, 1051)
    }

    for key, coords in actions.items():
        if key in command:
            x, y = coords
            pyautogui.moveTo(x, y)
            pyautogui.click()
            print(f"Executed: {key}")
            return f"{key.capitalize()} executed."

    print("Command not recognized.")
    return "Command not recognized."


def bring_to_foreground(app_name):
    """Brings the application window to the foreground (runs in a separate thread)."""
    try:
        # Use pywinauto to bring the application to the foreground
        app = Application(backend="win32").connect(title_re=f".{app_name}.", timeout=10)
        app.top_window().set_focus()  # Bring the window to the foreground
    except Exception:
        # If pywinauto fails, use ctypes to simulate Alt key press
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Press Alt key
        ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)  # Release Alt key

def open_application(app_name):
    """Opens the application and provides immediate feedback."""
    try:
        app_paths = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "file explorer": "explorer.exe",  # Or "explorer"
            "command prompt": "cmd.exe",       # Or "cmd"
            "paint": "mspaint.exe",          # Or "mspaint"
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",  # Correct path if needed
            "settings": "start ms-settings:",
            "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",  # Example VLC path
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE", # Example Word path - adjust Office version
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",  # Example Excel path - adjust Office version
            "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",# Example PowerPoint path - adjust Office version
        }
        matched_app = next((key for key in app_paths if key in app_name.lower()), None)

        if matched_app:
            # Special case for Windows settings
            if matched_app == "settings":
                os.system(app_paths[matched_app])  # Use os.system for settings
            else:
                # Open the application
                subprocess.Popen(app_paths[matched_app])

            # Run the foreground-focus logic in a separate thread
            threading.Thread(target=bring_to_foreground, args=(matched_app,)).start()

            response = f"Opening {matched_app}."
        else:
            response = f"Application '{app_name}' not found."

    except Exception as e:
        response = f"Error opening {app_name}: {str(e)}"

    # Update history
    update_conversation(f"open {app_name}", response)

    return response


def get_date_time():
    """Returns current day, date, and time"""
    now = datetime.datetime.now()
    day = now.strftime("%A")
    date = now.strftime("%d %B %Y")
    time = now.strftime("%I:%M %p")
    return f"Today is {day}, {date}, and the time is {time}."

def open_notifications():
    """Opens notification center in Windows"""
    pyautogui.hotkey('win', 'n')
    return "Opening notifications."


def window_action(action):
    """Improved window handling with focus management"""
    try:
        active_windows = gw.getWindowsWithTitle(gw.getActiveWindow().title)
        if not active_windows:
            return "No active window found."

        active_window = active_windows[0]  # Get the first match
        active_window.activate()  # Bring to focus

        if action == "minimize":
            active_window.minimize()
            return f"Minimized {active_window.title}"
        elif action == "maximize":
            active_window.restore()
            active_window.maximize()
            return f"Maximized {active_window.title}"
        elif action == "close":
            title = active_window.title
            active_window.close()
            return f"Closed {title}"
        return "Invalid window action"
    except Exception as e:
        print(f"Window Error: {e}")
        return "Failed to perform window action"

def get_weather():
    """Fetches weather details for the set city and provides a voice response."""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("cod") == 200:
            weather_desc = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            response_text = f"Today's weather: {weather_desc}, {temp} degrees Celsius."
        else:
            response_text = "Error: City not found or API issue."

    except Exception as e:
        response_text = "Error: Unable to fetch weather data."

    # Speak and update conversation history
    
    update_conversation("What's the weather like?", response_text)
    return response_text

def adjust_volume(command):
    if "increase" in command:
        pyautogui.press("volumeup")
    elif "decrease" in command:
        pyautogui.press("volumedown")
    elif "mute" in command:
        pyautogui.press("volumemute")

def adjust_brightness(command):
    try:
        current_brightness = sbc.get_brightness()[0]
        if "increase" in command:
            sbc.set_brightness(min(100, current_brightness + 10))
        elif "decrease" in command:
            sbc.set_brightness(max(0, current_brightness - 10))
    except:
        pass


def play_youtube_music(song_name):
    """Searches for a song on YouTube Music and plays it directly."""
    search_query = song_name.replace("play", "").replace("on youtube music", "").strip()
    videos_search = VideosSearch(search_query, limit=1)
    result = videos_search.result()
    
    if result and "result" in result:
        video_results = result.get("result", [])
        if video_results:
            first_video = video_results[0]
            song_url = first_video["link"]
            
            # Open YouTube Music with the song URL
            webbrowser.open(f"https://music.youtube.com/watch?v={song_url.split('v=')[-1]}")
            time.sleep(5)  # Wait for the page to load
            
            # Press space to start playing (ensures correct song is played)
            pyautogui.press('space')  

            response = f"Playing {search_query} on YouTube Music."
        else:
            response = f"Could not find {search_query} on YouTube Music."
    else:
        response = f"Could not find {search_query} on YouTube Music."

    # Give voice and text response
    update_conversation(f"play {song_name} on youtube music", response)

    return response


def play_on_youtube(search_query):
    videos_search = VideosSearch(search_query, limit=1)
    result = videos_search.result()
    
    if result and "result" in result:
        video_results = result.get("result", [])
        if video_results:
            first_video = video_results[0]
            webbrowser.open(first_video["link"])
            return f"Playing {search_query} on YouTube."
    
    # Ensure search_query is used in fallback
    webbrowser.open(f"https://www.youtube.com/results?search_query={search_query}")
    return f"Searching for {search_query} on YouTube."


def get_battery_status():
    """Gets battery percentage"""
    battery = psutil.sensors_battery()
    percent = battery.percent
    plugged = "plugged in" if battery.power_plugged else "not plugged in"
    return f"Battery is at {percent}% and is {plugged}."

def get_volume_status():
    """Gets system volume percentage"""
    try:
        # Initialize audio controller
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,  # Fixed from .iid to ._iid_
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        return f"Volume is at {int(volume.GetMasterVolumeLevelScalar() * 100)}%."
    except Exception as e:
        print(f"Volume Error: {e}")
        return "Unable to get volume level."

def get_brightness_status():
    """Gets screen brightness percentage"""
    try:
        brightness = sbc.get_brightness()[0]
        return f"Brightness is at {brightness}%."
    except:
        return "Unable to get brightness level."




@app.route('/get-history', methods=['GET'])
def get_history():
    return jsonify(conversation_history)





USERS_FILE = 'users.csv'  # CSV file storing registered users
HISTORY_FILE = 'history.csv'  # CSV file storing chat history

# Function to check user credentials from users.csv
def check_credentials(email, password):
    try:
        with open(USERS_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 3:  # Ensure row has username, email, and password
                    stored_username, stored_email, stored_password = row
                    if stored_email == email and stored_password == password:
                        return True  # Credentials match
    except FileNotFoundError:
        print("Error: users.csv file not found!")
    return False  # No match found

# Route to display login page (default route)
@app.route('/')
def index():
    return redirect(url_for('show_login'))

# Route to show login page
@app.route('/login')
def show_login():
    return render_template('login.html')

# Route to handle login functionality
# Route to handle login functionality
# Route to handle login functionality
@app.route('/login', methods=['POST'])
def user_login():
    name=request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
     

    if email == 'admin@gmail.com' and password == 'SAM@123':
        session['admin'] = True
        return redirect(url_for('admin_page'))  # Redirect to admin page
    
    with open('users.csv', 'r') as file:
        import csv
        reader = csv.reader(file)
        users = list(reader)
        user = next((row for row in users if row[1] == email), None)

    if not user:
        flash("Email does not exist", "danger")
        return redirect(url_for('show_login'))

    if user[2] != password:
        flash("Incorrect password", "danger")
        return redirect(url_for('show_login'))

    if check_credentials(email, password):
        session['email'] = email
        with open('users.csv', 'r') as file:
            import csv
            reader = csv.reader(file)
            for row in reader:
                if row[1] == email and row[2] == password:
                    session['name'] = row[0]   # Name
                    session['email'] = row[1]  # Email
                    print(f"Stored in session: {session['name']}, {session['email']}")
        flash("Login successful!", "success")
        return redirect(url_for('chat'))  # Redirect to chat page

    flash("Invalid email or password", "error")
    return redirect(url_for('show_login'))  # Redirect back to login page



@app.route('/admin')
def admin_page():
    if not session.get('admin'):
        return redirect(url_for('show_login'))
    return render_template('admin.html')


# Read users from CSV and return only names and emails
@app.route('/get_users')  # Updated route name

def get_users():
    users = []
    try:
        with open('users.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:  # Ensure row has at least name and email columns
                    users.append({
                        'name': row[0].strip(),  # Strip spaces to avoid empty values
                        'email': row[1].strip()
                    })
    except Exception as e:
        print(f"Error reading users.csv: {e}")
    return jsonify(users)


# Function to read users from CSV
def read_users():
    users = {}
    if not os.path.exists("users.csv"):
        return users  # Return empty if file doesn't exist
    
    with open("users.csv", mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) != 3:  # Skip invalid rows
                print(f"Skipping invalid row: {row}")  # Debugging output
                continue
            username, email, password = row
            users[email] = {"name": username, "password": password}
    return users


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        users = read_users()

        if email in users:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match. Try again.", "danger")
            return redirect(url_for("register"))

        # Save user to CSV
        with open("users.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([name, email, password])

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# Route to get user profile data for JavaScript

@app.route('/get_user_info')
def get_user_info():
    if 'name' in session and 'email' in session:
        return jsonify({'name': session['name'], 'email': session['email']})
    else:
        return jsonify({'error': 'User not logged in'}), 401


@app.route('/logout')
def logout():
    session.clear()
    flash("logout sucessfully", "danger")
    return redirect(url_for('show_login'))



@app.route('/login', methods=['GET', 'POST'])  # <-- Make sure this route exists
def login():
    return render_template("login.html")

# Function to read users from users.csv
def read_users():
    users = {}
    if not os.path.exists("users.csv"):
        return users  
    
    with open("users.csv", mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) != 3:
                continue
            username, email, password = row
            users[email] = {"name": username, "password": password}
    return users


# Function to save messages to history.csv
def save_message(email, session_id, message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(HISTORY_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([email, session_id, message, timestamp])

# Function to load chat history
def load_chat_history(email):
    chat_sessions = {}
    try:
        with open(HISTORY_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                row_email, session_id, message, timestamp = row
                if row_email == email:
                    if session_id not in chat_sessions:
                        chat_sessions[session_id] = []
                    chat_sessions[session_id].append({'message': message, 'timestamp': timestamp})
    except FileNotFoundError:
        pass
    return chat_sessions

# Route to handle user profile
def get_user_details(email):
    with open(USERS_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[1] == email:  # Checking email in the CSV
                return {"username": row[0], "email": row[1]}
    return None  # Return None if user not found




@app.route('/command', methods=['POST'])
def command_endpoint():
    user_command = request.json.get("command")
    print(f"User command received: {user_command}")  # Debugging log
    if not user_command:
        return jsonify({"response": "Command missing", "status": "error"}), 400
    
    global latest_command
    latest_command = user_command.lower().strip()
    response = process_command(latest_command)
    return jsonify({"response": response, "status": "success"})




@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'GET':
        if 'email' not in session:
            return redirect(url_for('login'))
        return render_template('chat.html')

    if request.method == 'POST':
        user_input = request.json.get("message", "")
        response = f"Sam: You said '{user_input}'"
        return jsonify({"response": response})






def start_listening():
    """Continuously listens for voice commands and processes them"""
    while True:
        command = listen()
        if command:
            print(f"Processing command: {command}")  # Debugging log
            response = process_command(command)
            print(f"Response generated: {response}")  # Debugging log
            time.sleep(1)  # Prevent CPU overloading & allow voice execution





#stop button

@app.route('/stop', methods=['POST'])
def stop():
    """Immediately stop current response"""
    global is_responding, tts_engine
    
    is_responding = False
    
    # Directly stop TTS engine if active
    if tts_engine:
        try:
            tts_engine.stop()
            tts_engine = None
        except:
            pass
    
    return jsonify({"status": "stopped", "message": "Response stopped"})


@app.route('/start-listening', methods=['POST'])
def start_listening_route():
    threading.Thread(target=start_wake_word_listening, daemon=True).start()
    return jsonify({"response": "Listening started!"})

# Start the Flask application
if __name__ == "__main__":
 
    # Start wake word detection in background
    wake_word_thread = threading.Thread(target=start_wake_word_listening, daemon=True)
    wake_word_thread.start()
    print("Running Flask server...")
    app.run(host="127.0.0.1", port=8080, debug=True, use_reloader=False)
