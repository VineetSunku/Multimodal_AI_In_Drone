from flask import Flask, render_template, request, jsonify
import cv2
from DroneFunctions.basicMoves import *
from DroneLogger import log
from mavsdk import System

######### ESTABLISHING CONNECTION #########

# Initialize UAV
uav = System()

# Connects to the UAV
async def connect_to_uav():
    await uav.connect(system_address="udp://:14540")

    log.debug("Establishing Connection...")
    async for state in uav.core.connection_state():
        if state.is_connected:
            log.info("UAV target UUID: {%s}", state.uuid) #Prints the UUID of the UAV to which the system connected
            break

    log.debug("Establishing GPS lock on UAV..")
    #Checks the gps Connection via telemetry health command
    async for health in uav.telemetry.health():
        if health.is_global_position_ok:
            log.info("Established GPS lock...")#GPS health approved
            break

app = Flask(__name__)
camera = cv2.VideoCapture(0)

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/video')
def video():
    return "1"
    # return Response(getVideo(), mimetype='multipart/x-mixed-replace; boundary=frame')

def getVideo():
    while True:
        ifCamera, frame = camera.read()
        if not ifCamera:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/keypressed', methods=['POST'])
async def keypressed():
    data = request.get_json()
    keyDir = data['value']
    if keyDir == "wd":
        log.info("Here!")
        await connect_to_uav()
    elif keyDir == "ad":
        print("a is pressed")
        await arm_and_takeoff(uav, 2.50)
    elif keyDir == "sd":
        print("s is pressed")
    elif keyDir == "ad":
        print("a is pressed")
    elif keyDir == "dd":
        print("d is pressed")
    elif keyDir == "wu":
        print("w is up")
    elif keyDir == "au":
        print("a is up")
    elif keyDir == "su":
        print("s is up")
    elif keyDir == "du":
        print("d is up")
    
    return jsonify(data)     

if __name__ == '__main__':
    app.run(debug=True)