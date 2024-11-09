import threading
import cv2
import asyncio
import track_obj


# Global variables to manage the thread and stop event
tracking_thread = None
stop_event = threading.Event()

def start_tracking_thread( input_bbox, drone):
    """Start the object tracking in a separate thread."""
    global tracking_thread, stop_event
    stop_event.clear()  # Reset the stop event

    async def tracking_wrapper():
        await track_obj.track_object_in_video(input_bbox, drone)

    # Function to start the asyncio event loop in a thread
    def run_in_thread():
        asyncio.run(tracking_wrapper())

    # Start the thread
    tracking_thread = threading.Thread(target=run_in_thread, daemon=True)
    tracking_thread.start()
    print("Tracking thread started.")

def stop_tracking_thread():
    """Stop the object tracking thread."""
    global tracking_thread, stop_event
    stop_event.set()  # Set the stop event to signal the thread to stop
    if tracking_thread is not None:
        tracking_thread.join()  # Wait for the thread to finish
        tracking_thread = None
  
    print("Tracking thread stopped.")
