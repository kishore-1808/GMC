import os
import sys

folder = os.path.dirname(os.path.abspath(sys.argv[0]))
os.chdir(folder)

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyautogui
import pygame
import random
import os
import time
import numpy as np
from collections import deque
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)

screen_width, screen_height = pyautogui.size()

BaseOptions = python.BaseOptions
HandLandmarkerOptions = vision.HandLandmarkerOptions
HandLandmarker = vision.HandLandmarker
ImageFormat = mp.ImageFormat
Image = mp.Image

script_dir = os.path.dirname(os.path.abspath(__file__))
gesture_dir = os.path.join(script_dir, '..', 'gesture_mouse_controller')
gesture_dir = os.path.normpath(gesture_dir)
model_path = os.path.join(gesture_dir, 'hand_landmarker.task')
sound_path = os.path.join(gesture_dir, "click_sound.mp3")

base_options = BaseOptions(model_asset_path=model_path)
options = HandLandmarkerOptions(
    base_options=base_options, 
    num_hands=1,
    min_hand_detection_confidence=0.3,
    min_hand_presence_confidence=0.3,
    min_tracking_confidence=0.3
)
hand_landmarker = HandLandmarker.create_from_options(options)

pygame.init()
pygame.mixer.init()

click_cooldown = 0.15
last_click_time = 0
screenshot_cooldown = 2.0
last_screenshot_time = 0

smooth_x, smooth_y = screen_width // 2, screen_height // 2
smoothing = 0.5

screenshot_folder = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
os.makedirs(screenshot_folder, exist_ok=True)

position_history = deque(maxlen=5)
pinch_start_time = None
pinch_required_time = 1.0
screenshot_taken_this_pinched = False
scroll_cooldown = 0.12
last_scroll_time = 0
volume_cooldown = 0.2
last_volume_time = 0
prev_scroll_y = None

current_action = "NONE"
mouse_control_enabled = False

def smooth_move(new_x, new_y):
    global smooth_x, smooth_y, position_history
    position_history.append((new_x, new_y))
    avg_x = sum(p[0] for p in position_history) / len(position_history)
    avg_y = sum(p[1] for p in position_history) / len(position_history)
    smooth_x = smooth_x + (avg_x - smooth_x) * smoothing
    smooth_y = smooth_y + (avg_y - smooth_y) * smoothing
    return int(smooth_x), int(smooth_y)

def check_finger_up(landmarks, tip_idx, pip_idx):
    return landmarks[tip_idx].y < landmarks[pip_idx].y

def check_pinched(landmarks):
    dist = ((landmarks[4].x - landmarks[8].x)**2 + (landmarks[4].y - landmarks[8].y)**2)**0.5
    return dist < 0.07

def move_mouse(landmarks):
    global smooth_x, smooth_y
    if landmarks:
        x, y = smooth_move(int(landmarks[8].x * screen_width), int(landmarks[8].y * screen_height))
        pyautogui.moveTo(x, y)

def do_click(click_type):
    global last_click_time
    current_time = time.time()
    if current_time - last_click_time > click_cooldown:
        if click_type == "left":
            pyautogui.click()
        elif click_type == "right":
            pyautogui.rightClick()
        elif click_type == "double":
            pyautogui.doubleClick()
        last_click_time = current_time
        return True
    return False

def play_sound():
    try:
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()
    except:
        pass

def do_screenshot():
    global last_screenshot_time
    current_time = time.time()
    if current_time - last_screenshot_time > screenshot_cooldown:
        path = os.path.join(screenshot_folder, f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}_{random.randint(1,100000)}.png")
        pyautogui.screenshot().save(path)
        threading.Thread(target=play_sound, daemon=True).start()
        last_screenshot_time = current_time
        return True
    return False

def volume_control(action):
    global last_volume_time
    current_time = time.time()
    if current_time - last_volume_time > volume_cooldown:
        keys = {"up": "volumeup", "down": "volumedown", "mute": "volumemute"}
        pyautogui.press(keys.get(action, ""))
        last_volume_time = current_time
        return True
    return False

def do_scroll(direction):
    global last_scroll_time
    current_time = time.time()
    if current_time - last_scroll_time > scroll_cooldown:
        pyautogui.scroll(500 if direction == "up" else -500)
        last_scroll_time = current_time
        return True
    return False

def process_gestures(landmarks, frame):
    global pinch_start_time, screenshot_taken_this_pinched, prev_scroll_y, current_action
    
    if not landmarks:
        current_action = "NONE"
        return None
    
    index_up = check_finger_up(landmarks, 8, 6)
    middle_up = check_finger_up(landmarks, 12, 10)
    ring_up = check_finger_up(landmarks, 16, 14)
    pinky_up = check_finger_up(landmarks, 20, 18)
    is_pinched = check_pinched(landmarks)
    
    action = None
    
    if is_pinched:
        current_time = time.time()
        if pinch_start_time is None:
            pinch_start_time = current_time
            screenshot_taken_this_pinched = False
        
        remaining = max(0, pinch_required_time - (current_time - pinch_start_time))
        cv2.rectangle(frame, (400, 100), (600, 140), (0, 0, 0), -1)
        cv2.putText(frame, f"Hold: {remaining:.1f}s", (410, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        if current_time - pinch_start_time >= pinch_required_time and not screenshot_taken_this_pinched:
            if do_screenshot():
                action = "SCREENSHOT"
                screenshot_taken_this_pinched = True
    
    elif index_up and ring_up and not middle_up and not pinky_up:
        if prev_scroll_y is not None:
            diff = prev_scroll_y - landmarks[8].y
            if diff > 0.012 and do_scroll("up"):
                action = "SCROLL UP"
            elif diff < -0.012 and do_scroll("down"):
                action = "SCROLL DOWN"
        prev_scroll_y = landmarks[8].y
            
    elif pinky_up and not index_up and not middle_up and not ring_up:
        if volume_control("down"):
            action = "VOLUME DOWN"
            
    elif index_up and middle_up and ring_up and pinky_up and not is_pinched:
        if volume_control("up"):
            action = "VOLUME UP"
            
    elif middle_up and ring_up and pinky_up and not index_up:
        if volume_control("mute"):
            action = "MUTE"
            
    elif index_up and middle_up and not ring_up and not pinky_up:
        if do_click("right"):
            action = "RIGHT CLICK"
            
    elif index_up and not middle_up and not ring_up and not pinky_up and not is_pinched:
        prev_scroll_y = None
        if mouse_control_enabled:
            move_mouse(landmarks)
        action = "MOVE"
        
    elif middle_up and not index_up and not ring_up and not pinky_up:
        prev_scroll_y = None
        if do_click("left"):
            action = "LEFT CLICK"
            
    elif index_up and middle_up and ring_up and not pinky_up:
        prev_scroll_y = None
        if do_click("double"):
            action = "DOUBLE CLICK"
    else:
        prev_scroll_y = None
    
    current_action = action if action else "NONE"
    return action

def draw_hand(frame, landmarks):
    if not landmarks:
        return
    h, w = frame.shape[:2]
    for start, end in [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(0,17),(17,18),(18,19),(19,20)]:
        pt1, pt2 = landmarks[start], landmarks[end]
        cv2.line(frame, (int(pt1.x*w), int(pt1.y*h)), (int(pt2.x*w), int(pt2.y*h)), (0,255,0), 2)
    for lm in landmarks:
        cv2.circle(frame, (int(lm.x*w), int(lm.y*h)), 6, (0,0,255), -1)

def generate_frames():
    global current_action, pinch_start_time, screenshot_taken_this_pinched, prev_scroll_y, mouse_control_enabled
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Camera not available")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    pyautogui.FAILSAFE = False
    
    time.sleep(1)
    
    ret, frame = cap.read()
    if not ret:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            ret, frame = cap.read()
            if not ret:
                continue

        original_frame = frame.copy()
        frame = cv2.flip(frame, 1)
        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=frameRGB)
        
        result = hand_landmarker.detect(mp_image)
        
        action = None
        display_action = "NO HAND"
        
        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            draw_hand(frame, landmarks)
            action = process_gestures(landmarks, frame)
            display_action = current_action if current_action != "NONE" else "READY"
        else:
            pinch_start_time = None
            screenshot_taken_this_pinched = False
            prev_scroll_y = None
            current_action = "NONE"

        cv2.rectangle(frame, (0, 0), (350, 40), (0, 0, 0), -1)
        cv2.putText(frame, "Gesture Control", (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

        colors = {
            "RIGHT CLICK": (0,0,255), 
            "SCREENSHOT": (255,0,255), 
            "DOUBLE CLICK": (0,255,255), 
            "VOLUME UP": (255,255,0), 
            "VOLUME DOWN": (255,255,0), 
            "MUTE": (255,255,0),
            "SCROLL UP": (0,255,255), 
            "SCROLL DOWN": (0,255,255),
            "MOVE": (0,255,0),
            "LEFT CLICK": (0,255,0)
        }
        
        color = colors.get(display_action, (80,80,80))
        
        cv2.rectangle(frame, (150, 100), (490, 160), (0, 0, 0), -1)
        cv2.rectangle(frame, (150, 100), (490, 160), color, 2)
        
        text_size = cv2.getTextSize(display_action, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        cv2.putText(frame, display_action, (text_x, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        ret2, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret2:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/enable_control', methods=['POST'])
def enable_control():
    global mouse_control_enabled
    mouse_control_enabled = True
    return jsonify({'status': 'enabled'})

@app.route('/disable_control', methods=['POST'])
def disable_control():
    global mouse_control_enabled
    mouse_control_enabled = False
    return jsonify({'status': 'disabled'})

@app.route('/get_action', methods=['GET'])
def get_action():
    return jsonify({'action': current_action})

@app.route('/trigger', methods=['POST'])
def trigger():
    data = request.get_json()
    action = data.get('action', '')
    if action == 'screenshot':
        if do_screenshot():
            return jsonify({'status': 'success'})
    return jsonify({'status': 'unknown'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
