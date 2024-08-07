import asyncio
from mavsdk import System
from mavsdk.offboard import PositionNedYaw
from mavsdk.action import Action

async def move_north(distance_m):
    # Connect to the drone
    drone = System()
    await drone.connect(system_address="udp://:14540")

    # Arm the drone
    await drone.action.arm()
    await asyncio.sleep(1)  # Wait for the drone to be armed

    # Take off to an altitude of 10 meters
    await drone.action.takeoff()
    await asyncio.sleep(10)  # Wait for the drone to reach the altitude

    # Start Offboard mode
    await drone.offboard.set_position_ned(
        north_m=0,
        east_m=0,
        down_m=-10,  # Move up to 10 meters altitude
        yaw_deg=0
    )
    await drone.offboard.start()
    await asyncio.sleep(1)  # Wait for Offboard mode to start

    # Move north by 10 meters
    await drone.offboard.set_position_ned(
        north_m=distance_m,
        east_m=0,
        down_m=0,
        yaw_deg=0
    )
    await asyncio.sleep(10)  # Wait for the drone to move

    # Land the drone
    await drone.a
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(move_north(10))