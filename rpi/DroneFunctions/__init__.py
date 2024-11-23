import asyncio
from mavsdk.offboard import PositionNedYaw, Attitude
from mavsdk import System
import math
from DroneLogger import log
import random
######### GLOBAL CONSTANTS #########

isPressed = True

######### TELEMETRY DETAILS #########
# Get Vehicle Co-ordinates
async def get_coord(uav: System):
    async def actualTelemetry(): 
        async for position in uav.telemetry.position():
            latitude = position.latitude_deg
            longitude = position.longitude_deg
            altitude = position.relative_altitude_m
            return latitude, longitude, altitude
    try:
        await asyncio.wait_for(actualTelemetry(), timeout=1)
    except Exception as e:
        log.error("Couldn't get actual coordinates. Generating random ones: "+ str(e))
    latitude, longitude, altitude = round(random.random(),5), round(random.random(),5), round(random.random(),5)
    await asyncio.sleep(0.1)
    return latitude, longitude, altitude

async def isArmed(uav: System):
    log.info("Checking if UAV is armed...")
    async for armed in uav.telemetry.armed():
        if armed:
            log.info("UAV is armed")
            return True
        log.warning("UAV is not yet armed!")
        return False

async def get_position_ned(uav: System):
    async for pos in uav.telemetry.position_velocity_ned():
        North = pos.position.north_m or 0
        East = pos.position.east_m or 0
        Down = pos.position.down_m or 0
        return North, East, Down
    return 0,0,0

async def get_attitude_body(uav: System):
    async for att in uav.telemetry.attitude_euler():
        Roll = att.roll_deg or 0
        Pitch = att.pitch_deg or 0
        Yaw = att.yaw_deg or 0
        return Roll, Pitch, Yaw
    return 0,0,0

async def get_flight_mode(uav: System):
    async for flight_mode in uav.telemetry.flight_mode():
        return str(flight_mode)


######### CONTROLLER ONLY MOVEMENTS #########

# Adjust Yaw
async def adjust_yaw(uav: System, dir):
    log.debug("adjusting yaw angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.debug(f"Recieved Attitude: Roll: {roll}  Pitch: {pitch}  Yaw: {yaw}", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.debug("Starting OFFBOARD MODE")
        await uav.offboard.start()
        count = 0
        global isPressed
        isPressed = True
        if dir=="right":
            while isPressed:
                yaw += 1
                if yaw>180:
                    yaw-=360
                await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5 ))
                await asyncio.sleep(0.01)
                count += 1
        else:
            while isPressed:
                yaw -=1
                if yaw<-180:
                    yaw+=360
                await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5 ))
                await asyncio.sleep(0.01)
                count += 1
    except Exception as e:
        log.error(e)
 
    
######### CONTROLLER AND AI MOVEMENTS #########

#  Arm and Takeoff
async def arm_and_takeoff(uav: System, alt: float):
    log.info("in arm and takeoff")
    log.info("Disabling Preflight checks")
    await uav.param.set_param_int("ARMING_CHECK", 0)
    await asyncio.sleep(1)
    log.info("Arming")
    await uav.action.arm()
    await asyncio.sleep(5)
    print("UAV is armed")
    print("Setting Takeoff altitude")
    north, east, down = await get_position_ned(uav)
    log.info(f"Noth: {north}, East: {east}, Down: {down}")
    await uav.action.set_takeoff_altitude(alt)
    await asyncio.sleep(3)  # Wait for 5 seconds to stabilize
    print("Taking Off")
    try:
        await uav.action.takeoff()
        await asyncio.sleep(5)  # Wait for 5 seconds to stabilize
    except Exception as e:
        print("takeoff failed?", e)

# Land UAV
async def land_uav(uav: System):
    log.info("LANDING")
    await uav.action.land()
    log.info("Landing complete. Disarming.")
    await asyncio.sleep(3)
    try:
        await uav.action.disarm()
    except:
        log.error("COULD NOT DISARM! OVERRIDE USING MANUAL CONTROL")

# Adjust Throttle
async def adjust_throttle(uav: System, throttle):
    log.debug("adjusting throttle angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.info(f"Recieved Attitude: Roll: {roll}  Pitch: {pitch}  Yaw: {yaw}")
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.debug("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        log.info("Adjusting Throttle")
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, throttle ))
        await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)

# Adjust Pitch 
async def adjust_pitch(uav: System, pit):
    log.debug("adjusting pitch angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.debug("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.debug("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        log.info("Adjusting Pitch")
        await uav.offboard.set_attitude(Attitude(roll, pit, yaw, 0.5 ))
        await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)    

#Adjust Roll  
async def adjust_roll(uav: System, rol):
    log.debug("adjusting roll angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.debug("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.debug("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        log.info("Adjusting Roll")
        await uav.offboard.set_attitude(Attitude(rol, pitch, yaw, 0.5 ))
        await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)    

# Stop Offboard Mode
async def stop_offboard(uav: System):
    global isPressed
    isPressed = False
    log.debug("Stopping OFFBOARD mode")
    try:
        await uav.offboard.stop()
    except Exception as e:
        log.error(e)
    
    
######### AI ONLY MOVEMENTS #########

# Hover
async def hover(duration):
    log.info(f"Hovering for {duration} seconds")
    await asyncio.sleep(duration)

# Move Right
async def move_right(uav: System, distance_m):
    log.debug("Moving Right")
    try:
        north, east, down = await get_position_ned(uav)
        roll, pitch, yaw = await get_attitude_body(uav)
        log.debug("Recieved Position: North: %s  East: %s Down: %s", north, east, down)
        log.debug("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw))
        # 0 degrees is assumed North
        north -= distance_m * math.sin(math.radians(yaw))
        east += distance_m * math.cos(math.radians(yaw))
        log.debug("Attempting to set new NED Co-ordinates: North: %s East: %s Down: %s", north, east, down)
        await uav.offboard.start()
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw ))
        await asyncio.sleep(1)
        await stop_offboard(uav)
        log.info("Moved Right by %s meters", distance_m)
    except Exception as e:
        log.error(e)
    
# Move Left
async def move_left(uav: System, distance_m):
    log.debug("Moving Left")
    try:
        north, east, down = await get_position_ned(uav)
        roll, pitch, yaw = await get_attitude_body(uav)
        log.debug("Recieved Position: North: %s  East: %s Down: %s", north, east, down)
        log.debug("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw))
        # 0 degrees is assumed North
        north += distance_m * math.sin(math.radians(yaw))
        east -= distance_m * math.cos(math.radians(yaw))
        log.debug("Attempting to set new NED Co-ordinates: North: %s East: %s Down: %s", north, east, down)
        await uav.offboard.start()
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw ))
        await asyncio.sleep(1)
        await stop_offboard(uav)
        log.info("Moved Left by %s meters", distance_m)
    except Exception as e:
        log.error(e)

# Move Forward
async def move_forward(uav: System, distance_m):
    log.debug("Moving Forward")
    try:
        north, east, down = await get_position_ned(uav)
        roll, pitch, yaw = await get_attitude_body(uav)
        log.debug("Recieved Position: North: %s  East: %s Down: %s", north, east, down)
        log.debug("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw))
        # 0 degrees is assumed North
        north += distance_m * math.cos(math.radians(yaw))
        east += distance_m * math.sin(math.radians(yaw))
        log.debug("Attempting to set new NED Co-ordinates: North: %s East: %s Down: %s", north, east, down)
        await uav.offboard.start()
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw ))
        await asyncio.sleep(1)
        await stop_offboard(uav)
        log.info("Moved Forward by %s meters", distance_m)
    except Exception as e:
        log.error(e)

# Move Backward
async def move_backward(uav: System, distance_m):
    log.debug("Moving Backward")
    try:
        north, east, down = await get_position_ned(uav)
        roll, pitch, yaw = await get_attitude_body(uav)
        log.debug("Recieved Position: North: %s  East: %s Down: %s", north, east, down)
        log.debug("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw))
        # 0 degrees is assumed North
        north -= distance_m * math.cos(math.radians(yaw))
        east -= distance_m * math.sin(math.radians(yaw))
        log.debug("Starting OFFBOARD MODE")
        await uav.offboard.start()
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw ))
        await asyncio.sleep(1)
        await stop_offboard(uav)
        log.info("Moved Backward by %s meters", distance_m)
    except Exception as e:
        log.error(e)

# Move Up
async def move_up(uav: System, distance_m):
    current_lat, current_lon, current_alt = await get_coord(uav)

    new_alt = current_alt + distance_m

    await uav.action.goto_location(current_lat, current_lon, new_alt, new_alt)
    log.info(f"Moved {distance_m} meters up to new location: Latitude: {current_lat}, Longitude: {current_lon}, Altitude: {new_alt}")

# Move Down
async def move_down(uav: System, distance_m):
    current_lat, current_lon, current_alt = await get_coord(uav)

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
        
# Adjust Yaw
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
        await uav.offboard.set_attitude(Attitude(roll, pitch, (ya+yaw +180)%360-180, 0.5 ))
        await asyncio.sleep(3)
        await stop_offboard(uav)
    except Exception as e:
        log.error(e)  