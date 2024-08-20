import asyncio
from DroneLogger import log
from mavsdk.offboard import OffboardError, PositionNedYaw, Attitude
from mavsdk import System
from mavsdk import telemetry
import math

######### GLOBAL CONSTANTS #########

isPressed = True
# Earth radius in meters
EARTH_RADIUS = 6378137.0


######### TELEMETRY DETAILS #########
# Get Vehicle Co-ordinates
async def get_coord(uav: System):
    log.debug("Retrieving Co-ordinates...")
    async for position in uav.telemetry.position():
        latitude = position.latitude_deg
        longitude = position.longitude_deg
        altitude = position.relative_altitude_m
        break
    log.info("Retrieved Coordinates: %s, %s, %s", latitude, longitude, altitude)
    return latitude, longitude, altitude

async def isArmed(uav: System):
    log.info("Checking if UAV is armed...")
    async for armed in uav.telemetry.armed():
        if armed:
            log.info("UAV is armed")
            return True
        log.warn("UAV is not yet armed!")
        return False

async def get_position_ned(uav: System):
    async for pos in uav.telemetry.position_velocity_ned():
        North = pos.position.north_m
        East = pos.position.east_m
        Down = pos.position.down_m
        return North, East, Down

async def get_attitude_body(uav: System):
    async for att in uav.telemetry.attitude_euler():
        Roll = att.roll_deg
        Pitch = att.pitch_deg
        Yaw = att.yaw_deg
        return Roll, Pitch, Yaw

async def get_flight_mode(uav: System):
    async for flight_mode in uav.telemetry.flight_mode():
        return str(flight_mode)


######### CONTROLLER ONLY MOVEMENTS #########

# Adjust Yaw
async def adjust_yaw(uav: System, dir):
    log.debug("adjusting yaw angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.info("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.info("Starting OFFBOARD MODE")
        await uav.offboard.start()
        count = 0
        global isPressed
        isPressed = True
        if dir=="left":
            while isPressed:
                yaw += 1
                if yaw>180:
                    yaw-=360
                await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.72 ))
                await asyncio.sleep(0.01)
                count += 1
        else:
            while isPressed:
                yaw -=1
                if yaw<-180:
                    yaw+=360
                await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.72 ))
                await asyncio.sleep(0.01)
                count += 1
    except Exception as e:
        log.error(e)
 
    
######### CONTROLLER AND AI MOVEMENTS #########

#  Arm and Takeoff
async def arm_and_takeoff(uav: System, alt: float):
    if not await isArmed(uav):
        log.warn("UAV is not yet armed! Arming UAV...")
        await uav.action.arm()
    log.info("UAV is armed")
    log.debug("Setting Takeoff altitude")
    await uav.action.set_takeoff_altitude(altitude=alt)
    log.info("Taking Off")
    await uav.action.takeoff()
    await asyncio.sleep(10)  # Wait for 10 seconds to stabilize

# Land UAV
async def land_uav(uav: System):
    log.info("LANDING")
    await uav.action.land()

# Adjust Throttle
async def adjust_throttle(uav: System, throttle):
    log.debug("adjusting throttle angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.info("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.info("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, throttle ))
        await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)

# Adjust Pitch 
async def adjust_pitch(uav: System, pit):
    log.debug("adjusting pitch angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.info("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.info("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        await uav.offboard.set_attitude(Attitude(roll, pit, yaw, 0.74 ))
        await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)    

#Adjust Roll  
async def adjust_roll(uav: System, rol):
    log.debug("adjusting roll angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.info("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.info("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        await uav.offboard.set_attitude(Attitude(rol, pitch, yaw, 0.74 ))
        await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)    

# Stop Offboard Mode
async def stop_offboard(uav: System):
    global isPressed
    isPressed = False
    await uav.offboard.stop()
    
    
######### AI ONLY MOVEMENTS #########

# Hover
async def hover(duration):
    log.info(f"Hovering for {duration} seconds")
    await asyncio.sleep(duration)

# Move Right
async def move_right(uav: System, distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    delta_lon = (distance_m / EARTH_RADIUS) * (180 / math.pi) / math.cos(current_lat * math.pi / 180)
    new_lon = current_lon + delta_lon

    await uav.action.goto_location(current_lat, new_lon, current_alt, current_alt)
    log.info(f"Moved {distance_m} meters right to new location: Latitude: {current_lat}, Longitude: {new_lon}, Altitude: {current_alt}")
    
# Move Left
async def move_left(uav: System, distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    delta_lon = (distance_m / EARTH_RADIUS) * (180 / math.pi) / math.cos(current_lat * math.pi / 180)
    new_lon = current_lon - delta_lon

    await uav.action.goto_location(current_lat, new_lon, current_alt, current_alt)
    log.info(f"Moved {distance_m} meters left to new location: Latitude: {current_lat}, Longitude: {new_lon}, Altitude: {current_alt}")

# Move Forward
async def move_forward(uav: System, distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    delta_lat = (distance_m / EARTH_RADIUS) * (180 / math.pi)
    new_lat = current_lat + delta_lat

    await uav.action.goto_location(new_lat, current_lon, current_alt, current_alt)
    log.info(f"Moved {distance_m} meters forward to new location: Latitude: {new_lat}, Longitude: {current_lon}, Altitude: {current_alt}")

# Move Backward
async def move_backward(uav: System, distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    delta_lat = (distance_m / EARTH_RADIUS) * (180 / math.pi)
    new_lat = current_lat - delta_lat

    await uav.action.goto_location(new_lat, current_lon, current_alt, current_alt)
    log.info(f"Moved {distance_m} meters backward to new location: Latitude: {new_lat}, Longitude: {current_lon}, Altitude: {current_alt}")

# Move Up
async def move_up(uav: System, distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    new_alt = current_alt + distance_m

    await uav.action.goto_location(current_lat, current_lon, new_alt, new_alt)
    log.info(f"Moved {distance_m} meters up to new location: Latitude: {current_lat}, Longitude: {current_lon}, Altitude: {new_alt}")

# Move Down
async def move_down(uav: System, distance_m):
    current_lat, current_lon, current_alt = await get_coord()

    new_alt = current_alt - distance_m

    await uav.action.goto_location(current_lat, current_lon, new_alt, new_alt)
    log.info(f"Moved {distance_m} meters down to new location: Latitude: {current_lat}, Longitude: {current_lon}, Altitude: {new_alt}")

# Move to Custom Location
async def move_to_location(uav: System, x, y, z):
    log.debug(f"Moving to location ({x}, {y}, {z})")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        await uav.action.goto_location(x, y, z, yaw)
        log.info(f"Moved to location ({x}, {y}, {z})")
    except Exception as e:
        log.error(e)
        
# Adjust Throttle
async def adjust_yaw_ai(uav: System, ya):
    log.debug("adjusting yaw angle by AI")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.debug("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.debug("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        await uav.offboard.set_attitude(Attitude(roll, pitch, ya, 0.74 ))
        await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)