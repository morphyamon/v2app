import pickle
import cv2
import numpy as np
import pyautogui
import requests
import time
from threading import Thread
import queue

# Relay server information
RELAY_URL = "http://localhost:8080"  # Change this to your relay server address

# Configure PyAutoGUI for safety
pyautogui.FAILSAFE = True
# Optional: Add small delay between actions to prevent overwhelming the system
pyautogui.PAUSE = 0.1

def capture_screen():
    """Capture screen and encode it as JPEG"""
    try:
        # Take screenshot using pyautogui
        screenshot = pyautogui.screenshot()
        # Convert PIL image to numpy array
        screenshot_np = np.array(screenshot)
        # Convert RGB to BGR (OpenCV format)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        # Encode as JPEG
        _, img_encoded = cv2.imencode('.jpg', screenshot_bgr, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return img_encoded.tobytes()
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

def handle_client_messages():
    last_capture_time = 0
    min_capture_interval = 0.1  # Minimum time between captures in seconds
    
    while True:
        try:
            # Poll for client messages
            response = requests.get(f"{RELAY_URL}/server/poll", timeout=35)
            
            if response.status_code == 200:
                data = response.content
                
                if data == b"capture":
                    current_time = time.time()
                    # Check if enough time has passed since last capture
                    if current_time - last_capture_time >= min_capture_interval:
                        # Capture and send screen
                        img_data = capture_screen()
                        if img_data:
                            try:
                                # Send the image data to the relay server
                                requests.post(f"{RELAY_URL}/server/push", data=img_data)
                                last_capture_time = current_time
                            except requests.exceptions.RequestException as e:
                                print(f"Error sending image: {e}")
                
                else:
                    # Handle mouse click coordinates
                    try:
                        coordinates = pickle.loads(data)
                        print(f"Executing click at: {coordinates}")
                        # Get current screen size
                        screen_width, screen_height = pyautogui.size()
                        x, y = coordinates
                        
                        # Validate coordinates are within screen bounds
                        if 0 <= x <= screen_width and 0 <= y <= screen_height:
                            pyautogui.click(x, y)
                        else:
                            print(f"Click coordinates ({x}, {y}) out of bounds")
                            
                    except Exception as e:
                        print(f"Error processing coordinates: {e}")
                        
        except requests.exceptions.RequestException as e:
            print(f"Polling error: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(1)

def main():
    try:
        print("Starting Windows screen sharing server...")
        print(f"Connecting to relay server at {RELAY_URL}")
        print(f"Screen resolution: {pyautogui.size()}")
        
        # Start the message handling loop
        handle_client_messages()
        
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()