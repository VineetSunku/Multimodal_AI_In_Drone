import asyncio
from DroneLogger import log
from mavsdk.offboard import OffboardError, PositionNedYaw, Attitude
from mavsdk import System
from mavsdk import telemetry

######### GLOBAL CONSTANTS #########

isPressed = True

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

######### BASIC MOVEMENTS #########

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

async def adjust_throttle(uav: System, dir):
    log.debug("adjusting throttle angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.info("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.info("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        if dir=="up":
            await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.8 ))
            await asyncio.sleep(0.01)
        else:
            await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.4 ))
            await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)
    
async def adjust_pitch(uav: System, dir):
    log.debug("adjusting pitch angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.info("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.info("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        if dir=="forward":
            await uav.offboard.set_attitude(Attitude(roll, -20, yaw, 0.74 ))
            await asyncio.sleep(0.01)
        else:
            await uav.offboard.set_attitude(Attitude(roll, 20, yaw, 0.74 ))
            await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)    
    
async def adjust_roll(uav: System, dir):
    log.debug("adjusting roll angle")
    try:
        roll, pitch, yaw = await get_attitude_body(uav)
        log.info("Recieved Attitude: Roll: %s  Pitch: %s  Yaw: %s", roll, pitch, yaw)
        await uav.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.5))
        log.info("Starting OFFBOARD MODE")
        await uav.offboard.start()
        global isPressed
        isPressed = True
        if dir=="left":
            await uav.offboard.set_attitude(Attitude(-20, pitch, yaw, 0.74 ))
            await asyncio.sleep(0.01)
        else:
            await uav.offboard.set_attitude(Attitude(20, pitch, yaw, 0.74 ))
            await asyncio.sleep(0.01)
    except Exception as e:
        log.error(e)    
   
async def stop_offboard(uav: System):
    global isPressed
    isPressed = False
    await uav.offboard.stop()