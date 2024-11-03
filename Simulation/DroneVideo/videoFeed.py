from gz.transport13 import Node
from gz.msgs10.image_pb2 import Image  
import cv2
import numpy as np
from ultralytics import YOLO 
import time
from DroneLogger import log

global camera_frame
camera_frame = cv2.imread('DroneVideo/image.png') 

# Load the YOLOv10 model
model = YOLO('models/yolov10n.pt')  # Replace with the correct model size (n, s, m, b, l, x)

def yoloCallback(msg):
    
    # Extract image dimensions from the protobuf message
    width = msg.width
    height = msg.height
    channels = 3  # Assuming an RGB image, adjust if the image has a different number of channels
    
    # Convert the raw image data from protobuf to a numpy array
    img_data = np.frombuffer(msg.data, dtype=np.uint8)
    
    # Reshape the data to match the image dimensions
    image = img_data.reshape((height, width, channels))

    # Convert the image from BGR to RGB (if necessary) for YOLOv10 processing
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Perform object detection using YOLOv10
    results = model.predict(source=rgb_image, save=False, conf=0.25, show=False)  # Adjust confidence threshold if needed
    writable_image = np.copy(image)

    for result in results:
        boxes = result.boxes  # Get the bounding boxes
        for box in boxes: # type: ignore
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get the coordinates
            confidence = box.conf[0]  # Confidence score
            class_id = int(box.cls[0].item())  # Convert class_id to integer

            # Draw the bounding box on the writable image
            cv2.rectangle(writable_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(writable_image, f"{model.names[class_id]} {confidence:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        global camera_frame
        camera_frame = writable_image

def defaultCallback(msg):
     # Extract image dimensions from the protobuf message
    width = msg.width
    height = msg.height
    channels = 3  # Assuming an RGB image
    
    # Convert the raw image data from protobuf to a numpy array
    img_data = np.frombuffer(msg.data, dtype=np.uint8)
    
    # Reshape the data to match the image dimensions
    image = img_data.reshape((height, width, channels))

    # Update the global camera frame (no further processing)
    global camera_frame
    camera_frame = image

def main():
    # Create a Gazebo Transport node
    node = Node()

    # Define the camera topic
    topic = "/camera"

    # Subscribe to the camera topic using the Image protobuf message
    if node.subscribe(Image, topic, defaultCallback):
        log.info(f"Subscribing to type {Image} on topic [{topic}]")
    else:
        log.error(f"Error subscribing to topic [{topic}]")
        return

    log.info("retrieving camera_frame")
    global camera_frame
    # Keep the program alive to continue receiving data
    while True:
        ret, buffer = cv2.imencode('.jpg', camera_frame)
        frame = buffer.tobytes()
        time.sleep(0.001)
        yield frame
