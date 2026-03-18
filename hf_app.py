import gradio as gr
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from collections import deque
import os

BaseOptions = python.BaseOptions
HandLandmarkerOptions = vision.HandLandmarkerOptions
HandLandmarker = vision.HandLandmarker
ImageFormat = mp.ImageFormat
Image = mp.Image

model_path = "hand_landmarker.task"

base_options = BaseOptions(model_asset_path=model_path)
options = HandLandmarkerOptions(
    base_options=base_options, 
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
hand_landmarker = HandLandmarker.create_from_options(options)

smoothing = 0.25
position_history = deque(maxlen=10)

def check_finger_up(landmarks, tip_idx, pip_idx):
    return landmarks[tip_idx].y < landmarks[pip_idx].y

def draw_hand(frame, landmarks):
    if not landmarks:
        return frame
    h, w = frame.shape[:2]
    for start, end in [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(0,17),(17,18),(18,19),(19,20)]:
        pt1, pt2 = landmarks[start], landmarks[end]
        cv2.line(frame, (int(pt1.x*w), int(pt1.y*h)), (int(pt2.x*w), int(pt2.y*h)), (0,255,0), 2)
    for lm in landmarks:
        cv2.circle(frame, (int(lm.x*w), int(lm.y*h)), 5, (0,255,0), -1)
    return frame

def process_frame():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        frame = cv2.flip(frame, 1)
        
        try:
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = Image(image_format=ImageFormat.SRGB, data=frameRGB)
            result = hand_landmarker.detect(mp_image)
        except:
            continue
        
        action = "No Hand"
        
        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            frame = draw_hand(frame, landmarks)
            
            index_up = check_finger_up(landmarks, 8, 6)
            middle_up = check_finger_up(landmarks, 12, 10)
            ring_up = check_finger_up(landmarks, 16, 14)
            pinky_up = check_finger_up(landmarks, 20, 18)
            
            if index_up and not middle_up and not ring_up and not pinky_up:
                action = "Move Mouse"
            elif middle_up and not index_up and not ring_up and not pinky_up:
                action = "Left Click"
            elif index_up and middle_up and not ring_up and not pinky_up:
                action = "Right Click"
            elif index_up and middle_up and ring_up and not pinky_up:
                action = "Double Click"
            elif index_up and middle_up and ring_up and pinky_up:
                action = "Volume Up"
            elif pinky_up and not index_up and not middle_up and not ring_up:
                action = "Volume Down"
            elif middle_up and ring_up and pinky_up and not index_up:
                action = "Mute"
            else:
                action = "Ready"
        
        cv2.rectangle(frame, (0, 0), (300, 40), (0, 0, 0), -1)
        cv2.putText(frame, "Hand Gesture Recognition", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
        
        if action != "No Hand" and action != "Ready":
            color = (0, 255, 0)
            cv2.rectangle(frame, (180, 100), (460, 155), (0, 0, 0), -1)
            cv2.rectangle(frame, (180, 100), (460, 155), color, 2)
            cv2.putText(frame, action, (200, 138), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        ret2, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
        if ret2:
            yield buffer.tobytes()
    
    cap.release()

# Gradio Interface
with gr.Blocks(title="Hand Gesture Control") as demo:
    gr.Markdown("# 🖐️ Hand Gesture Recognition")
    gr.Markdown("Control your mouse with hand gestures in real-time!")
    
    video = gr.Video(format="jpeg", streaming=True)
    
    # Start video stream
    video.stream(process_frame, inputs=None, outputs=video)
    
    gr.Markdown("""
    ## Available Gestures
    - ✌️ Index Finger → Move Mouse
    - 🖕 Middle Finger → Left Click
    - ✌️🖕 Index + Middle → Right Click
    - ✌️🖕🫱 Index + Middle + Ring → Double Click
    - 🖐️ All 4 Fingers → Volume Up
    - 👈 Pinky → Volume Down
    - 🖕✌️👈 Middle + Ring + Pinky → Mute
    """)

demo.launch()
