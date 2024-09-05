from gz.transport13 import Node
from gz.msgs10.image_pb2 import Image  
import cv2
import numpy as np
import time
from ultralytics import YOLO 

# import os

# Load the YOLOv10 model
model = YOLO('models/yolov10n.pt')  # Replace with the correct model size (n, s, m, b, l, x)

def callback(msg):
    print("Received image data")
    
    # Extract image dimensions from the protobuf message
    width = msg.width
    height = msg.height
    channels = 3  # Assuming an RGB image, adjust if the image has a different number of channels
    
    # Convert the raw image data from protobuf to a numpy array
    img_data = np.frombuffer(msg.data, dtype=np.uint8)
    
    # Reshape the data to match the image dimensions
    try:
        image = img_data.reshape((height, width, channels))

        # Convert the image from BGR to RGB (if necessary) for YOLOv10 processing
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Perform object detection using YOLOv10
        results = model.predict(source=rgb_image, save=False, conf=0.25, show=False)  # Adjust confidence threshold if needed
        writable_image = np.copy(image)

        # current_directory = os.getcwd()

        # public_directory = os.path.join(current_directory, 'public')

        # if not os.path.exists(public_directory):
        #     os.makedirs(public_directory)

        # # Define the full path for the new image
        # image_path = os.path.join(public_directory, 'new_image_name.jpg')

        # # Save the image
        # writable_image.save(image_path)

        # print(f"Image saved to {image_path}")
        # Draw bounding boxes and labels on the image
        for result in results:
            boxes = result.boxes  # Get the bounding boxes
            for box in boxes: # type: ignore
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get the coordinates
                confidence = box.conf[0]  # Confidence score
                class_id = int(box.cls[0].item())  # Convert class_id to integer

                # Draw the bounding box on the writable image
                cv2.rectangle(writable_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(writable_image, f"{model.names[class_id]} {confidence:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the image with detections
        cv2.imshow("Camera Feed with YOLOv10 Detections", writable_image)
        cv2.waitKey(1)
    except ValueError as e:
        print(f"Failed to reshape and decode image: {e}")
    except KeyError as e:
        print(f"Failed to retrieve class name for class_id {class_id}: {e}")

def main():
    # Create a Gazebo Transport node
    node = Node()

    # Define the camera topic
    topic = "/camera"

    # Subscribe to the camera topic using the Image protobuf message
    if node.subscribe(Image, topic, callback):
        print(f"Subscribing to type {Image} on topic [{topic}]")
    else:
        print(f"Error subscribing to topic [{topic}]")
        return

    # Keep the program alive to continue receiving data
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    print("Done")

if __name__ == '__main__':
    main()
