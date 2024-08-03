######DEPENDENCIES############
import google.generativeai as genai
import re
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
from math import cos, radians
import argparse

# Specify the file path
file_path = 'prompt.txt'

# Open and read the file
with open(file_path, 'r') as file:
    content = file.read()


#########FUNCTIONS########
def connectMyCopter():
    parser = argparse. ArgumentParser (description='commands')
    parser.add_argument('--connect')
    args = parser.parse_args()
    connection_string = args.connect
    vehicle = connect (connection_string, wait_ready=True)
    return vehicle 


######MAIN EXECUTABLE#######
vehicle = connectMyCopter()

def arm_and_takeoff(vehicle, target_altitude):
    print("Basic pre-arm checks")
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(target_altitude)

    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= target_altitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)

def land_drone(vehicle):
    print("Landing")
    vehicle.mode = VehicleMode("LAND")
    while vehicle.armed:
        print(" Waiting for disarming...")
        time.sleep(1)

    print("Landed and disarmed")

def move_forward(vehicle, distance):
    print("Moving forward")
    current_location = vehicle.location.global_relative_frame
    target_location = LocationGlobalRelative(current_location.lat + (distance / 6371000.0), current_location.lon, current_location.alt)
    vehicle.simple_goto(target_location)
    time.sleep(distance / vehicle.airspeed)

def move_backward(vehicle, distance):
    print("Moving backward")
    current_location = vehicle.location.global_relative_frame
    target_location = LocationGlobalRelative(current_location.lat - (distance / 6371000.0), current_location.lon, current_location.alt)
    vehicle.simple_goto(target_location)
    time.sleep(distance / vehicle.airspeed)

def move_left(vehicle, distance):
    print("Moving left")
    current_location = vehicle.location.global_relative_frame
    target_location = LocationGlobalRelative(current_location.lat, current_location.lon - (distance / (6371000.0 * cos(current_location.lat))), current_location.alt)
    vehicle.simple_goto(target_location)
    time.sleep(distance / vehicle.airspeed)

def move_right(vehicle, distance):
    print("Moving right")
    current_location = vehicle.location.global_relative_frame
    target_location = LocationGlobalRelative(current_location.lat, current_location.lon + (distance / (6371000.0 * cos(current_location.lat))), current_location.alt)
    vehicle.simple_goto(target_location)
    time.sleep(distance / vehicle.airspeed)

def move_up(vehicle, distance):
    print("Moving up")
    current_location = vehicle.location.global_relative_frame
    target_location = LocationGlobalRelative(current_location.lat, current_location.lon, current_location.alt + distance)
    vehicle.simple_goto(target_location)
    time.sleep(distance / vehicle.airspeed)

def move_down(vehicle, distance):
    print("Moving down")
    current_location = vehicle.location.global_relative_frame
    target_location = LocationGlobalRelative(current_location.lat, current_location.lon, current_location.alt - distance)
    vehicle.simple_goto(target_location)
    time.sleep(distance / vehicle.airspeed)

genai.configure(api_key="AIzaSyAy2SyA5e0uXjiPM6QZ160OGNuMYGmVpYY")

model = genai.GenerativeModel('gemini-1.5-flash')

messages = [
        {'role':'model',
        'parts': ["You are an assistant helping me with the SITL simulator for the Tello drone. When I ask you to do something, you are supposed to give me Python code that is needed to achieve that task using the DroneBlocks simulator and then an explanation of what that code does. You are only allowed to use the functions I have defined for you. You are not to use any other hypothetical functions that you think might exist."]}
    ]
messages.append({
            'role':'user',
            'parts':[content]
})
res = model.generate_content(messages)
print(res.text);

code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)

def extract_python_code(content):
    code_blocks = code_block_regex.findall(content)
    if code_blocks:
        full_code = "\n".join(code_blocks)

        if full_code.startswith("python"):
            full_code = full_code[7:]

        return full_code
    else:
        return None

class colors:  
    RED = "\033[31m"
    ENDC = "\033[m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"

while True:
    ques = input(colors.YELLOW + "Dronekit ChatBot> " + colors.ENDC)
   
    if ques=="exit":
     break
    
    messages.append({'role':'user',
                    'parts':[ques]})
    
    response = model.generate_content(messages)
    gen_code = extract_python_code(response.text)
    exec(gen_code)
    print(response.text)
print("Successfully exited the chatbot")    