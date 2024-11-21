import cv2
import asyncio
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import time
from DroneFunctions import *

model = YOLO("yolov10n.pt")
tracker = DeepSort(max_age=30, n_init=2, nn_budget=100)

# Constants
FLAG_OBJECT_TRACKING= True
REFERENCE_OBJECT_SIZE= 4000
REFERENCE_OBJECT_TOLERANCE= 500
DEFAULT_BACKWARD_MOVEMENT= -1
DEFAULT_FORWARD_MOVEMENT= 1
FRAME_CENTER_TOLERANCE = 20  # tolerance in pixels to consider as centered
LOST_OBJECT_TIMEOUT = 4  # time in seconds to trigger drone rotation when object is not detected
FRAME_PROCESS_INTERVAL = 1  # process frames at 1-second intervals

def calculate_iou(boxA, boxB):
    """Calculate the Intersection over Union (IoU) of two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def detect_and_track_object(frame, input_bbox):
    """Runs YOLO on the frame and uses DeepSORT for tracking."""
    results = model(frame)
    max_iou = 0
    best_detection = None
    
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detected_bbox = [x1, y1, x2, y2]
            score = float(box.conf[0])
            class_id = int(box.cls[0])
            iou = calculate_iou(input_bbox, detected_bbox)
            if iou > max_iou:
                max_iou = iou
                best_detection = ([x1, y1, x2, y2], score, class_id)

    tracks = []
    if best_detection:
        tracks = tracker.update_tracks([best_detection], frame=frame)
    return tracks

async def calculate_movement(frame, track, uav):
    """Calculate movement commands based on the object's position and command the drone accordingly."""
    # Frame and bounding box dimensions
    frame_height, frame_width = frame.shape[:2]
    frame_center_x, frame_center_y = frame_width // 2, frame_height // 2

    # Bounding box coordinates
    x1, y1, w, h = track.to_ltwh()
    x1, y1, x2, y2 = int(x1), int(y1), int(x1 + w), int(y1 + h)
    x_center, y_center = (x1 + x2) // 2, (y1 + y2) // 2

    # Calculate offsets from the frame center
    offset_x = x_center - frame_center_x
    offset_y = y_center - frame_center_y

    # Calculate distance adjustment
    object_bb_size = (w * h)
    if abs(object_bb_size-REFERENCE_OBJECT_SIZE)>REFERENCE_OBJECT_TOLERANCE:
        if object_bb_size > REFERENCE_OBJECT_TOLERANCE:
            distance_diff=DEFAULT_BACKWARD_MOVEMENT
        else:
            distance_diff=DEFAULT_FORWARD_MOVEMENT   
    else:
        distance_diff=0
    # Horizontal and vertical adjustments (left/right and up/down)
    if abs(offset_x) > FRAME_CENTER_TOLERANCE:
        if offset_x > 0:
            # await move_right(uav, abs(offset_x) / frame_width)  # Move right proportional to offset
            await move_right(uav, 1)  # Move right proportional to offset
            
        else:
            # await move_left(uav, abs(offset_x) / frame_width)  # Move left proportional to offset
            await move_left(uav, 1)  # Move left proportional to offset

    if abs(offset_y) > FRAME_CENTER_TOLERANCE:
        if offset_y > 0:
            # await move_down(uav, abs(offset_y) / frame_height)  # Move down proportional to offset
            await move_down(uav, 1)  # Move down proportional to offset
            
        else:
            # await move_up(uav, abs(offset_y) / frame_height)  # Move up proportional to offset
            await move_up(uav, 1)  # Move up proportional to offset

    # Forward/backward adjustment based on safe distance
    if distance_diff > 0:
        await move_forward(uav, abs(distance_diff))  # Move forward if too far
    elif distance_diff < 0:
        await move_backward(uav, abs(distance_diff))  # Move backward if too close

    track_id = track.track_id
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(frame, f'Track ID: {track_id}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return  


async def start_object_tracking( input_bbox, drone: System):
    input_bbox = [input_bbox[1],input_bbox[0],input_bbox[3],input_bbox[2]]
    input_bbox = [i/1000*640 if i%2==0 else i/1000*480 for i in input_bbox]
    last_seen_time = time.time()
    global REFERENCE_OBJECT_SIZE, FLAG_OBJECT_TRACKING
    REFERENCE_OBJECT_SIZE= (input_bbox[2]-input_bbox[0])*(input_bbox[3]-input_bbox[1])
    frame = cv2.imread("./logs/drone_feed.jpg")
    ret = frame is not None
    while FLAG_OBJECT_TRACKING and ret:
        log.info("trying to track")
        if not ret:
            break

        current_time = time.time()
        if current_time - last_seen_time < FRAME_PROCESS_INTERVAL:
            continue

        tracks = detect_and_track_object(frame, input_bbox)

        if any(track.is_confirmed() for track in tracks):
            last_seen_time = current_time
            for track in tracks:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue

                await calculate_movement(frame, track, drone)
                
        

    cv2.destroyAllWindows()

def stop_tracking():
    global FLAG_OBJECT_TRACKING
    FLAG_OBJECT_TRACKING=False
    log.info("Sent command to stop tracking")


# Usage example in another script
# asyncio.run(track_object_in_video(0, [100, 200, 400, 500], None))
