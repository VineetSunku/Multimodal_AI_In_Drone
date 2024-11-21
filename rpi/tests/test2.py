import asyncio
from mavsdk import System, action
from mavsdk.offboard import VelocityNedYaw, OffboardError,PositionNedYaw
import math
import sys

async def run():
    uav = System()
    await uav.connect(system_address="serial:///dev/ttyAMA0:57600")

    print("Establishing Connection...")

    try:
        # Check connection state with a timeout
        async for state in uav.core.connection_state():
            if state.is_connected:
                print("Established Connection")
                break
            await asyncio.sleep(1)
        else:
            print("Failed to establish connection.")
    except asyncio.TimeoutError:
        print("Connection timed out.")
    
    async for health in uav.telemetry.health():
        print(health)
        if not health.is_armable:
            print("Disabling Preflight checks")
            await uav.param.set_param_int("ARMING_CHECK", 0)
            await asyncio.sleep(2)
        # await uav.param.set_param_int("ARMING_CHECK", 1)
        break
    
    try:
        print("Arming the uav...")
        await uav.action.arm()
    except Exception as e:
        print("Didnt arm: ", e)
        sys.exit()
    
    await asyncio.sleep(5)

    north, east, down = await get_position_ned(uav)
    print(f"Noth: {north}, East: {east}, Down: {down}")
    
    try:
        await uav.action.set_takeoff_altitude(3)
    except:
        print("altitude didnt work")
    
    try:
        print("taking off")
        await uav.action.takeoff()
    except Exception as e:
        print("Takeoff didnt work", e)
    
    await asyncio.sleep(5)
    _ = input("Press enter to move:")
    print("now moving forward")
    await move_forward(uav, 10)
    print("moved forward")
    
    await asyncio.sleep(5)
    _ = input("Press enter to land:")
    print("Landing")
    await uav.action.land()
    
    await asyncio.sleep(5)
    print("disarming")
    await uav.action.disarm()
        
        
async def move_forward(uav: System, distance_m):
    try:
        north, east, down = await get_position_ned(uav)
        roll, pitch, yaw = await get_attitude_body(uav)
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw))
        # 0 degrees is assumed North
        north += distance_m * math.cos(math.radians(yaw))
        east += distance_m * math.sin(math.radians(yaw))
        await uav.offboard.start()
        await uav.offboard.set_position_ned(PositionNedYaw(north, east, down, yaw ))
        await asyncio.sleep(3)
        await stop_offboard(uav)
    except Exception as e:
        print(e)

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


async def stop_offboard(uav: System):
    global isPressed
    isPressed = False
    await uav.offboard.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())