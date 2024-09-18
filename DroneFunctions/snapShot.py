from gz.transport13 import Node
from gz.msgs10 import image_pb2 as gz_image_pb2
import cv2
import numpy as np
import time
from ultralytics import YOLO
import os
from datetime import datetime

# Load the YOLOv10 model
model = YOLO('yolov10n.pt')  

# Global variable to keep track of whether the image has been captured
image_captured = False

def callback(msg: gz_image_pb2.Image):
    global image_captured

    if image_captured:
        return

    print("Received image data")
    
    # Extract image dimensions from the protobuf message
    width = msg.width
    height = msg.height
    channels = 3  # Assuming an RGB image
    
    # Convert the raw image data from protobuf to a numpy array
    img_data = np.frombuffer(msg.data, dtype=np.uint8)
    
    # Reshape the data to match the image dimensions
    try:
        image = img_data.reshape((height, width, channels))

        # Convert the image from BGR to RGB (if necessary) for YOLOv10 processing
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Perform object detection using YOLOv10
        results = model.predict(source=rgb_image, save=False, conf=0.25, show=False)
        writable_image = np.copy(image)

        # Draw bounding boxes and labels on the image
        for result in results:
            boxes = result.boxes  # Get the bounding boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get the coordinates
                confidence = box.conf[0]  # Confidence score
                class_id = int(box.cls[0].item())  # Convert class_id to integer

                # Draw the bounding box on the writable image
                cv2.rectangle(writable_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(writable_image, f"{model.names[class_id]} {confidence:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        
        public_directory = "../logs/public"

        if not os.path.exists(public_directory):
            os.makedirs(public_directory)

        # Define the full path for the new image
        timestamp = datetime.now().strftime('%m%d_%H')
        image_name = f"image_{timestamp}.jpg"
        image_path = os.path.join(public_directory, image_name)

        
        cv2.imwrite(image_path, writable_image)
        print(f"Image saved to {image_path}")

        # Mark that we've captured the image
        image_captured = True

        # Stop the main loop
        cv2.destroyAllWindows()

    except ValueError as e:
        print(f"Failed to reshape and decode image: {e}")
    except KeyError as e:
        print(f"Failed to retrieve class name for class_id {class_id}: {e}")

def main():
    global image_captured

    # Create a Gazebo Transport node
    node = Node()

    # Define the camera topic
    topic = "/camera"

    # Subscribe to the camera topic using the Image protobuf message
    if node.subscribe(gz_image_pb2.Image, topic, callback):
        print("")
    else:
        print(f"Error subscribing to topic [{topic}]")
        return

    # Wait until the image is captured, then exit
    while not image_captured:
        time.sleep(1)

    print("Image capture complete. Exiting.")
    print("     *************\n")

if __name__ == '__main__':
    main()
