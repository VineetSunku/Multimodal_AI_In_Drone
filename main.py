import asyncio
from mavsdk import System
import google.generativeai as genai
import re
import time
import math
import argparse

######### GLOBAL CONSTANTS #########

# Earth radius in meters
EARTH_RADIUS = 6378137.0

######### ESTABLISHING CONNECTION #########
# Specify the file path
file_path = 'prompt.txt'

# Open and read the file
with open(file_path, 'r') as file:
    content = file.read()


uav = System()

# Connects to the UAV
async def connect_to_uav():
    
    await uav.connect(system_address="udp://:14540")

    print("Establishing Connection...")
    async for state in uav.core.connection_state():
        if state.is_connected:
            print("UAV target UUID: {state.uuid}") #Prints the UUID of the UAV to which the system connected
            break

    print("Establishing GPS lock on UAV..")
    #Checks the gps Connection via telemetry health command
    async for health in uav.telemetry.health():
        if health.is_global_position_ok:
            print("Established GPS lock...")#GPS health approved
            break


######### TELEMETRY DETAILS #########
# Get Vehicle Co-ordinates
async def get_coord():
    async for position in uav.telemetry.position():
        latitude = position.latitude_deg
        longitude = position.longitude_deg
        altitude = position.relative_altitude_m
        break
    return latitude, longitude, altitude

async def isArmed():
    async for armed in uav.telemetry.armed():
        if armed:
            return True
        return False
    
######### BASIC MOVEMENTS #########
# Arm and Takeoff
async def arm_and_takeoff(altitude):
    if not await isArmed():
        print("Arming UAV")
        await uav.action.arm()
        print("Taking Off")
        await uav.action.takeoff()
        await asyncio.sleep(10)  # Wait for 10 seconds to stabilize
        lat, long, alt = await get_coord()
        print(f"Ascending to {altitude} meters")
        await uav.action.goto_location(lat, long, altitude, 0)
    

# Hover
async def hover( duration):
    print(f"Hovering for {duration} seconds")
    await asyncio.sleep(duration)

# Land UAV
async def land_uav():
    print("LANDING")
    await uav.action.land()

# Move Right
async def move_right(distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    delta_lon = (distance_m / EARTH_RADIUS) * (180 / math.pi) / math.cos(current_lat * math.pi / 180)
    new_lon = current_lon + delta_lon

    await uav.action.goto_location(current_lat, new_lon, current_alt, current_alt)
    print(f"Moved {distance_m} meters right to new location: Latitude: {current_lat}, Longitude: {new_lon}, Altitude: {current_alt}")

# Move Left
async def move_left( distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    delta_lon = (distance_m / EARTH_RADIUS) * (180 / math.pi) / math.cos(current_lat * math.pi / 180)
    new_lon = current_lon - delta_lon

    await uav.action.goto_location(current_lat, new_lon, current_alt, current_alt)
    print(f"Moved {distance_m} meters left to new location: Latitude: {current_lat}, Longitude: {new_lon}, Altitude: {current_alt}")

# Move Forward
async def move_forward( distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    delta_lat = (distance_m / EARTH_RADIUS) * (180 / math.pi)
    new_lat = current_lat + delta_lat

    await uav.action.goto_location(new_lat, current_lon, current_alt, current_alt)
    print(f"Moved {distance_m} meters forward to new location: Latitude: {new_lat}, Longitude: {current_lon}, Altitude: {current_alt}")

# Move Backward
async def move_backward(distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    delta_lat = (distance_m / EARTH_RADIUS) * (180 / math.pi)
    new_lat = current_lat - delta_lat

    await uav.action.goto_location(new_lat, current_lon, current_alt, current_alt)
    print(f"Moved {distance_m} meters backward to new location: Latitude: {new_lat}, Longitude: {current_lon}, Altitude: {current_alt}")

# Move Up
async def move_up( distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    new_alt = current_alt + distance_m

    await uav.action.goto_location(current_lat, current_lon, new_alt, new_alt)
    print(f"Moved {distance_m} meters up to new location: Latitude: {current_lat}, Longitude: {current_lon}, Altitude: {new_alt}")

# Move Down
async def move_down( distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    new_alt = current_alt - distance_m

    await uav.action.goto_location(current_lat, current_lon, new_alt, new_alt)
    print(f"Moved {distance_m} meters down to new location: Latitude: {current_lat}, Longitude: {current_lon}, Altitude: {new_alt}")

# Move to Custom Location
async def move_to_location( x, y, z):
    print(f"Moving to location ({x}, {y}, {z})")
    await uav.action.goto_location(x, y, z, 0)


######### GEN-AI CONFIGURATION #########
genai.configure(api_key="")
safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

model = genai.GenerativeModel('gemini-1.5-flash',safety_settings=safety_settings)

messages = [
        {'role':'model',
        'parts': ["You are an assistant helping me with the gazebo simulator for the Tello uav. " + 
                  "When I ask you to do something, you are supposed to give me Python code that is needed " + 
                  "to achieve that task using the gazebo simulator and then an explanation of what that code does. " + 
                  "You are only allowed to use the functions I have defined for you. " + 
                  "You are not to use any other hypothetical functions that you think might exist."]}
    ]
messages.append({
            'role':'user',
            'parts':[content]
})
res = model.generate_content(messages)

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

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_to_uav())
    while True:
        ques = input(colors.YELLOW + "uavkit ChatBot> " + colors.ENDC)
    
        if ques=="exit":
            break
        
        messages.append({'role':'user', 'parts':[ques]})
        
        response = model.generate_content(messages)
        gen_code = extract_python_code(response.text)

        print(response.text)
        exec(gen_code)
    print("Successfully exited the chatbot")    

