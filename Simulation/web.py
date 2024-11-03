import asyncio
from flask import Flask, render_template, request, jsonify, Response
from mavsdk import System
import threading
from DroneFunctions.basicMoves import *
import csv
import cv2
from flask_socketio import SocketIO
from DroneAI.Gemini import generate_response as generate_gemini_response
from DroneAI.LLAVA import generate_response as generate_llava_response
from DroneAI.VisionClassifier import visionClassifier as vc
from DroneVideo import videoFeed as vf
from DroneLogger import log
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

######### UAV CONNECTIONS ######### 
uav = System()

async def connect_to_uav():
    await uav.connect(system_address="udp://:14540")
    async for state in uav.core.connection_state():
        if state.is_connected:
            log.info("Connected to UAV")
            break

######### ASYNCIO AND THREADING #########

def run_in_loop(task):
    asyncio.run_coroutine_threadsafe(task, mainLoop)

######### READ CHATS #########

def read_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        return [row for row in reader]

######### APP ROUTES #########

@app.route('/')
def index():
    data = read_csv('./logs/chats.csv')
    return render_template('index.html', data=data)

@app.route('/takeoff', methods=['POST'])
def takeoff():
    #  Arm and Takeoff
    run_in_loop(arm_and_takeoff(uav, 2.5))
    return jsonify({"status": "Takeoff initiated"})

@app.route('/land', methods=['POST'])
def land():
    run_in_loop(land_uav(uav))
    return jsonify({"status": "Landing initiated"})

@app.route('/keypress', methods=['POST'])
def keyPressed():
    data = request.get_json()
    keyDir = data['value']
    if keyDir == "ld":
        run_in_loop(adjust_yaw(uav, "left"))
    elif keyDir == "rd":
        run_in_loop(adjust_yaw(uav, "right"))
    elif keyDir == "ud":
        run_in_loop(adjust_throttle(uav, 0.8))
    elif keyDir == "dod":
        run_in_loop(adjust_throttle(uav, 0.4))
    elif keyDir == "wd":
        run_in_loop(adjust_pitch(uav, -20))
    elif keyDir == "sd":
        run_in_loop(adjust_pitch(uav, 20))
    elif keyDir == "ad":
        run_in_loop(adjust_roll(uav, -20))
    elif keyDir == "dd":
        run_in_loop(adjust_roll(uav, 20))
    else:
        run_in_loop(stop_offboard(uav))
    return jsonify({"status": "Yaw initiated"})

@app.route('/send_message', methods=['POST'])
def sendMessage():
    data = request.get_json()
    ques = data['message']
    
    with open('./logs/chats.csv','a', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow([data['who'], data['message']])
    emit_update('person')
    
    requires_image = vc(ques)
    
    if data['VLM']=="true":
        if requires_image:
            log.info("Prompt requires image. Capturing Screenshot")
            gen_code = generate_gemini_response(ques, captureScreenshot())
        else:
            gen_code = generate_gemini_response(ques)
        emit_update('Gemini')
    else:
        if requires_image:
            log.info("Prompt requires image. Capturing Screenshot")
            gen_code = generate_llava_response(ques, captureScreenshot())
        else: 
            gen_code = generate_llava_response(ques)
        emit_update('LLaVA')

    if gen_code:
        exec(gen_code)
    return jsonify({'response': gen_code})
        
def emit_update(who):
    data = read_csv('./logs/chats.csv')
    socketio.emit(who, {'data': data[-1][1]})

######### VIDEO FEED #########

@app.route('/video')
def video():
    return Response(getVideo(), mimetype='multipart/x-mixed-replace; boundary=frame')

def getVideo():
    for frames in vf.main():
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frames + b'\r\n')

def captureScreenshot() -> str:
    """Saves a snapshot of the drone's camera feed."""
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S-%d:%m:%Y")
    os.chdir('./logs/images')
    cv2.imwrite(formatted_time + '.jpg', vf.camera_frame)
    log.info("Captured camera snaphot. View the image in logs.")
    os.chdir('../../')
    return "./logs/images/"+ formatted_time + '.jpg'
        

######### TELEMETRY #########

async def emit_coords(uav: System):
    while True:
        latitude, longitude, altitude = await get_coord(uav)
        # Emit the coordinates to the frontend
        socketio.emit('coordinates', {'lat': latitude, 'lon': longitude, 'alt': altitude})
        await asyncio.sleep(1)

if __name__ == '__main__':
    mainLoop = asyncio.get_event_loop()
    mainLoop.run_until_complete(connect_to_uav())
    threading.Thread(target=mainLoop.run_forever).start()
    run_in_loop(emit_coords(uav))
    
    socketio.run(app)
