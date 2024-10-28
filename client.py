import cv2
import socket
import pickle
import numpy as np
import time
import requests
from threading import Thread
import queue

# Relay server information
RELAY_URL = "http://localhost:8080"  # Change this to your relay server address
image_queue = queue.Queue(maxsize=1)  # Only keep the latest image

def poll_images():
    while True:
        try:
            response = requests.get(f"{RELAY_URL}/client/poll", timeout=35)
            if response.status_code == 200:
                img_data = response.content
                img_np = np.frombuffer(img_data, dtype=np.uint8)
                img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
                
                # Update the queue with the latest image
                if not image_queue.empty():
                    try:
                        image_queue.get_nowait()  # Remove old image
                    except queue.Empty:
                        pass
                image_queue.put(img)
        except requests.exceptions.RequestException as e:
            print(f"Polling error: {e}")
            time.sleep(1)

def click_event(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        coordinates = pickle.dumps((x, y))
        try:
            requests.post(f"{RELAY_URL}/client/push", data=coordinates)
            print(f"Sent coordinates: ({x}, {y})")
        except requests.exceptions.RequestException as e:
            print(f"Error sending coordinates: {e}")

# Start polling thread
polling_thread = Thread(target=poll_images, daemon=True)
polling_thread.start()

# Request initial capture
requests.post(f"{RELAY_URL}/client/push", data=b"capture")

# Main display loop
while True:
    try:
        # Get the latest image from the queue
        img = image_queue.get(timeout=1)
        
        # Show image and set callback for clicks
        cv2.imshow('Target Screen', img)
        cv2.setMouseCallback('Target Screen', click_event)
        
        # Refresh every 0.5 seconds, break on 'q' press
        if cv2.waitKey(500) & 0xFF == ord('q'):
            break
            
    except queue.Empty:
        continue
    except Exception as e:
        print(f"Error: {e}")
        break

cv2.destroyAllWindows()