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


async def connect_drone():
    # Connect to the drone and wait for connection
    # drone = System()
    # await drone.connect(system_address="udp://:14540")
    # async for state in drone.core.connection_state():
    #     if state.is_connected:
    #         print("Drone connected!")
    #         return drone
    pass


async def initialize_drone(drone):
    # Initialize offboard mode for precise control
    # await drone.offboard.set_position_ned(PositionNedYaw(0, 0, -1, 0))  # Start at 1 meter altitude
    # await drone.action.arm()
    # await asyncio.sleep(2)
    # try:
    #     await drone.offboard.start()
    # except OffboardError as e:
    #     print(f"Offboard start failed with error: {e._result.result}")
    #     await drone.action.disarm()
    pass


def detect_and_track_object(frame, object_name):
    """
    Runs YOLO on the frame and uses DeepSORT for tracking the specified object.
    Returns the list of tracks for the specified object and frame dimensions.
    """
    # Run YOLOv8 on the frame
    results = model(frame)

    # Filter detections for the specified object
    detections = []
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            label = model.names[class_id]
            if label.lower() == object_name.lower():
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                score = float(box.conf[0])
                detections.append(([x1, y1, x2, y2], score, class_id))

    # Update DeepSORT tracker
    tracks = tracker.update_tracks(detections, frame=frame)
    return tracks


def calculate_movement(frame, track, object_name):
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
    cv2.putText(frame, f'{object_name} ID: {track_id}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return forward_backward, left_right, up_down


async def rotate_drone_40_degrees(drone, current_angle):
    # Rotate drone by 40 degrees increment
    new_angle = current_angle + 40
    if new_angle >= 360:
        new_angle = 0  # Reset after full rotation

    # await drone.offboard.set_position_ned(PositionNedYaw(0, 0, -1, new_angle))
    print(f"Rotating to {new_angle} degrees")
    await asyncio.sleep(1)  # Time to stabilize after each rotation
    return new_angle


async def process_frames(cap, object_name, drone):
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

        # Detect and track object
        tracks = detect_and_track_object(frame, object_name)

        # Check if object is detected
        if any(track.is_confirmed() for track in tracks):
            # If object is detected, reset last_seen_time and stop rotation
            last_seen_time = current_time
            current_angle = 0  # Reset rotation
            for track in tracks:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue

                forward_backward, left_right, up_down = calculate_movement(frame, track, object_name)
                print(f"Movement - Forward/Backward: {forward_backward}, Left/Right: {left_right}, Up/Down: {up_down}")

        else:
            # If object is not detected and timeout has passed, rotate by 40 degrees
            if current_time - last_seen_time >= LOST_OBJECT_TIMEOUT:
                current_angle = await rotate_drone_40_degrees(drone, current_angle)
                last_seen_time = current_time  # Reset the timer after each rotation

                # If a full 360-degree rotation is completed, end the search rotation
                if current_angle == 0:
                    print("Completed full 360-degree rotation without finding the object.")
                    break

        # Show the frame
        cv2.imshow("Object Tracking", frame)

        # Break on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()


async def track_object(object_name):
    # Connect and initialize the drone
    # drone = await connect_drone()
    # await initialize_drone(drone)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error opening webcam.")
        return

    await process_frames(cap, object_name, None)  # Pass drone instance in place of None

    # Clean up
    # await drone.action.land()
    print("Landed and cleanup done.")


# Usage
object_name = input("Enter the object name to track: ")
asyncio.run(track_object(object_name))
