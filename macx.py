import pickle
import cv2
import numpy as np
import subprocess
import pyautogui
import requests
import time
from threading import Thread

# Relay server information
RELAY_URL = "http://localhost:8080"  # Change this to your relay server address

def handle_client_messages():
    while True:
        try:
            response = requests.get(f"{RELAY_URL}/server/poll", timeout=35)
            if response.status_code == 200:
                data = response.content
                
                if data == b"capture":
                    # Capture screenshot
                    screenshot_file = 'image.png'
                    subprocess.run(['screencapture', screenshot_file])

                    # Read and encode the captured image
                    screenshot = cv2.imread(screenshot_file)
                    screenshot_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
                    _, img_encoded = cv2.imencode('.jpg', screenshot_bgr)
                    img_data = img_encoded.tobytes()
                    
                    # Send the image data to the relay server
                    requests.post(f"{RELAY_URL}/server/push", data=img_data)
                else:
                    # Handle mouse click coordinates
                    try:
                        coordinates = pickle.loads(data)
                        print(f"Executing click at: {coordinates}")
                        pyautogui.click(coordinates)
                    except Exception as e:
                        print(f"Error processing coordinates: {e}")
                        
        except requests.exceptions.RequestException as e:
            print(f"Polling error: {e}")
            time.sleep(1)

print("Starting server...")
handle_client_messages()