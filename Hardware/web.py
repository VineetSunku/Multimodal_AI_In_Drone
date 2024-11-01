from flask import Flask, render_template, request, jsonify, Response
import time
import threading
import csv
from flask_socketio import SocketIO
from DroneAI.Gemini import generate_response as generate_gemini_response
from DroneAI.LLAVA import generate_response as generate_llava_response
from DroneAI.VisionClassifier import visionClassifier as vc
from DroneLogger import log
from AirConnect import SendToAir, SocketMessage, Sender, GroundType, CameraFrame, receiveTelemetry, ReceiveFromAir, save_screenshot

"""This is the main event loop that receives input from the web console and 
sends the results to the companion Computer. Not added explicitly in a seperate thread."""

################## Initial Setup ##################

app = Flask(__name__) #Flask app initialize
socketio = SocketIO(app) #Flask to JS socket initialize

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

@app.route('/buttonpress', methods=['POST'])
def buttonpress():
    data = request.get_json()
    button = data['value']
    SendToAir(SocketMessage(Sender.GROUND, GroundType.CONTROLLER, button))
    return jsonify({"status": "Takeoff or land initiated"})

@app.route('/keypress', methods=['POST'])
def keyPressed():
    data = request.get_json()
    keyDir = data['value']
    if keyDir[-1] == "d":
        SendToAir(SocketMessage(Sender.GROUND, GroundType.CONTROLLER, keyDir))
    else:
        SendToAir(SocketMessage(Sender.GROUND, GroundType.CONTROLLER, "so"))
    return jsonify({"status": "Key Pressed"})

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
            gen_code = generate_gemini_response(ques, save_screenshot())
        else:
            gen_code = generate_gemini_response(ques)
        emit_update('Gemini')
    else:
        if requires_image:
            log.info("Prompt requires image. Capturing Screenshot")
            gen_code = generate_llava_response(ques, save_screenshot())
        else: 
            gen_code = generate_llava_response(ques)
        emit_update('LLaVA')

    if gen_code:
        SendToAir(SocketMessage(Sender.GROUND, GroundType.AI, gen_code))
    return jsonify({'response': gen_code})

def emit_update(who):
    data = read_csv('./logs/chats.csv')
    socketio.emit(who, {'data': data[-1][1]})

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(CameraFrame(), mimetype='multipart/x-mixed-replace; boundary=frame')

def emit_coords():
    while True:
        latitude, longitude, altitude = receiveTelemetry()
        # Emit the coordinates to the frontend
        socketio.emit('coordinates', {'lat': latitude, 'lon': longitude, 'alt': altitude})
        time.sleep(1)
        
######### LOG DRONE OUTPUTS #########
def log_drone():
    while True:
        drone_message = ReceiveFromAir()
        if drone_message["level"] == "INFO":
            log.info(drone_message["message"])
        elif drone_message["level"] == "WARNING":
            log.warning(drone_message["message"])
        elif drone_message["level"] == "ERROR":
            log.error(drone_message["message"])
        elif drone_message["level"] == "DEBUG":
            log.debug(drone_message["message"])
            
if __name__ == '__main__':
    t2 = threading.Thread(target=emit_coords)
    t3 = threading.Thread(target=log_drone)
    t2.start()
    t3.start()
    socketio.run(app)
