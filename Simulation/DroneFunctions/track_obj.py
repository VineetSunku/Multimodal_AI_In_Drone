import cv2
import asyncio
from ultralytics import YOLO

from deep_sort_realtime.deepsort_tracker import DeepSort
import time

# Initialize YOLOv8 and DeepSORT
model = YOLO("yolov8n.pt")
tracker = DeepSort(max_age=30, n_init=2, nn_budget=100)

# Constants
SAFE_DISTANCE = 1.0  # desired distance from the object in meters
FRAME_CENTER_TOLERANCE = 20  # tolerance in pixels to consider as centered
LOST_OBJECT_TIMEOUT = 4  # time in seconds to trigger drone rotation when object is not detected
FRAME_PROCESS_INTERVAL = 1  # process frames at 1-second intervals

def calculate_iou(boxA, boxB):
    """Calculate the Intersection over Union (IoU) of two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    
    # Compute intersection area
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    
    # Compute the area of both bounding boxes
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    
    # Compute IoU
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def detect_and_track_object(frame, input_bbox):
    """
    Runs YOLO on the frame and uses DeepSORT for tracking the object that has the maximum
    overlap with the given input bounding box.
    """
    # Run YOLOv8 on the frame
    results = model(frame)

    # Filter detections based on maximum overlap with input bounding box
    max_iou = 0
    best_bbox = None
    best_detection = None
    
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detected_bbox = [x1, y1, x2, y2]
            score = float(box.conf[0])
            class_id = int(box.cls[0])

            # Calculate IoU with the input bounding box
            iou = calculate_iou(input_bbox, detected_bbox)
            if iou > max_iou:
                max_iou = iou
                best_bbox = detected_bbox
                best_detection = ([x1, y1, x2, y2], score, class_id)

    # Update DeepSORT tracker if a matching object is found
    tracks = []
    if best_detection:
        tracks = tracker.update_tracks([best_detection], frame=frame)
    return tracks

def calculate_movement(frame, track):
    """
    Calculate movement commands based on the object's position in the frame and safe distance.
    Returns movement values and updates the frame with bounding boxes and labels.
    """
    frame_height, frame_width = frame.shape[:2]
    frame_center_x, frame_center_y = frame_width // 2, frame_height // 2

    # Calculate bounding box center
    x1, y1, w, h = track.to_ltwh()
    x1, y1, x2, y2 = int(x1), int(y1), int(x1 + w), int(y1 + h)
    x_center, y_center = (x1 + x2) // 2, (y1 + y2) // 2

    # Calculate movement direction to keep object centered
    offset_x = x_center - frame_center_x
    offset_y = y_center - frame_center_y

    # Movement commands
    forward_backward = 0.0
    left_right = 0.0
    up_down = 0.0

    # Adjust horizontal position (left/right)
    if abs(offset_x) > FRAME_CENTER_TOLERANCE:
        left_right = -0.5 if offset_x > 0 else 0.5

    # Adjust vertical position (up/down)
    if abs(offset_y) > FRAME_CENTER_TOLERANCE:
        up_down = -0.5 if offset_y > 0 else 0.5

    # Maintain safe distance (1 meter)
    object_distance = 0.5 * (w + h)  # Approximate distance based on bounding box size
    if object_distance < SAFE_DISTANCE:
        forward_backward = -0.5  # Move backward
    elif object_distance > SAFE_DISTANCE:
        forward_backward = 0.5  # Move forward

    # Draw bounding box and ID
    track_id = track.track_id
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(frame, f'Track ID: {track_id}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return forward_backward, left_right, up_down

# Modify `process_frames` to use bounding box instead of object name
async def process_frames(cap, input_bbox, drone):
    last_seen_time = time.time()
    current_angle = 0  # Start rotation angle at 0 degrees

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Process frames every FRAME_PROCESS_INTERVAL seconds
        current_time = time.time()
        if current_time - last_seen_time < FRAME_PROCESS_INTERVAL:
            continue

        # Detect and track object based on bounding box
        tracks = detect_and_track_object(frame, input_bbox)

        # Check if object is detected
        if any(track.is_confirmed() for track in tracks):
            last_seen_time = current_time
            current_angle = 0  # Reset rotation
            for track in tracks:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue

                forward_backward, left_right, up_down = calculate_movement(frame, track)
                print(f"Movement - Forward/Backward: {forward_backward}, Left/Right: {left_right}, Up/Down: {up_down}")
        
        # Display the frame
        cv2.imshow("Object Tracking", frame)
        
        # Break on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# Usage example
input_bbox = [100, 200, 400, 500]  # Example bounding box coordinates
asyncio.run(process_frames(cv2.VideoCapture(0), input_bbox, None))#pass instance of drone in place of none
