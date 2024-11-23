import socket
from threading import Thread
import cv2
import asyncio
from DroneFunctions import *
from DroneFunctions.track_obj import start_object_tracking
from DroneLogger import log
from DroneCamera import CameraObject
######### UAV CONNECTIONS ######### 

async def connect_to_uav():
    try:
        await uav.connect(system_address="serial:///dev/ttyAMA0:57600")
        async for state in uav.core.connection_state():
            if state.is_connected:
                log.info("Connected to UAV")
                await asyncio.sleep(2)
                break
    except Exception as e:
        log.error(f"Failed to connect to Drone: {e}")
    
async def receive():
    log.info("Now receiving inputs")
    while True:
        try:
            print("waiting")
            d = eval(ground.recv(1024).decode())
            print("done waiting")
            if d['messageType'] == "Controller":
                keyDir = d['message']
                if keyDir == "takeoff":
                    log.info("Initiating Takeoff sequence")
                    await arm_and_takeoff(uav, 3)
                elif keyDir =="land":
                    await land_uav(uav)
                elif keyDir == "ld":
                    await adjust_yaw(uav, "left")
                elif keyDir == "rd":
                    await adjust_yaw(uav, "right")
                elif keyDir == "ud":
                    await adjust_throttle(uav, 0.8)
                elif keyDir == "dod":
                    await adjust_throttle(uav, 0.4)
                elif keyDir == "wd":
                    await adjust_pitch(uav, -20)
                elif keyDir == "sd":
                    await adjust_pitch(uav, 20)
                elif keyDir == "ad":
                    await adjust_roll(uav, -20)
                elif keyDir == "dd":
                    await adjust_roll(uav, 20)
                else:
                    await stop_offboard(uav)
            elif d["messageType"] == "AI":
                print(d)
                gen_code = d["message"]
                log.debug(gen_code) 
                exec_context = globals().copy()
                exec(gen_code, exec_context)
                ai_function = exec_context["ai_function"]
                await ai_function()
                log.info("Stopped Tracking")
        except Exception as e:
            print("Main Socket Connection Closed", e)
            break

def videoStream():
    log.info("Now sending video")
    try:
        while True:
            frame = camera.capture_array()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', frame)
            __, buffer1 = cv2.imencode('.jpg', frame_rgb)
            frame = buffer.tobytes()
            frame_rgb = buffer1.tobytes()
            with open("./logs/drone_feed.jpg", "wb") as file:
                file.write(frame_rgb)
            ground_video.sendall(len(frame).to_bytes(4, 'big'))
            ground_video.sendall(frame)
    except Exception as e:
        print(f"Video Socket Connection Closed: {e}")

async def main():
    global uav, log, ground, ground_video, camera, RPI_IP
    log.info("RPi is available to connect")
    uav = System()
    RPI_IP = "192.168.208.38"
    rpi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rpi.bind((RPI_IP, 4682))
    rpi.listen(1)

    ground, addr = rpi.accept()
    ground.send(f'Primary link established. You are {addr}'.encode())

    rpi_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rpi_video.bind((RPI_IP, 3461))
    rpi_video.listen(1)

    ground_video, addr_video = rpi_video.accept()
    ground_video.send("Video link established".encode())

    camera = CameraObject()

    await connect_to_uav()
    t1=Thread(target=videoStream)
    t1.start()
    await receive()

async def run_in_loop(fn):
    mainLoop = asyncio.get_event_loop()
    task = mainLoop.create_task(fn)
    await task
    
if __name__ == "__main__":
    asyncio.run(main())