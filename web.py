import asyncio
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from mavsdk import System
from mavsdk.manual_control import ManualControlResult
import threading
from DroneFunctions.basicMoves import *
import csv
import cv2
from flask_socketio import SocketIO, emit
from DroneAI.main import generate_response
from DroneVideo import videoFeed as vf

app = Flask(__name__)
socketio = SocketIO(app)

######### UAV CONNECTIONS ######### 
uav = System()
loop = asyncio.get_event_loop()

async def connect_to_uav():
    await uav.connect(system_address="udp://:14540")
    async for state in uav.core.connection_state():
        if state.is_connected:
            print(f"Connected to UAV")
            break

def run_in_loop(task):
    asyncio.run_coroutine_threadsafe(task, loop)

# Start the UAV connection in the main thread's event loop
loop.run_until_complete(connect_to_uav())

######### READ CHATS #########

def read_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        return [row for row in reader]

######### APP ROUTES #########

@app.route('/')
def index():
    data = read_csv('./logs/Chats.csv')
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
    with open('./logs/Chats.csv','a', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow([data['who'], data['message']])
    emit_update('person')
    gen_code = generate_response(data['message']) or ""
    emit_update('ai')
    exec(gen_code)
    return jsonify({'response': gen_code})
        
def emit_update(who):
    data = read_csv('./logs/Chats.csv')
    socketio.emit(who, {'data': data[-1][1]})

######### VIDEO FEED #########

@app.route('/video')
def video():
    return Response(getVideo(), mimetype='multipart/x-mixed-replace; boundary=frame')

def getVideo():
    for frames in vf.main():
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frames + b'\r\n')

if __name__ == '__main__':
    threading.Thread(target=loop.run_forever).start()
    socketio.run(app)
