import asyncio
from mavsdk import System
from math import pi,cos

HOME_LAT = 47.3980938273671
HOME_LONG = 8.54629063426236

def m_to_lat(dx,dy, lat, long):
    r_earth = 6366707.0195
    new_latitude  = lat  + (dy / r_earth) * (180 / pi)
    new_longitude = long + (dx / r_earth) * (180 / pi) / cos(lat * pi/180)
    return (new_latitude,new_longitude)

async def run():
    uav = System()
    await uav.connect(system_address="udp://:14540")

    print("Establishing Connection...")
    async for  state in uav.core.connection_state():
        if state.is_connected:
            print(f"Established Connection")
            break

    print("Establishing GPS lock on UAV..")
    #Checks the gps Connection via telemetry health command
    async for health in uav.telemetry.health():
        if health.is_global_position_ok:
            print("Established GPS lock...")#GPS health approved
            break
        
    print("Arming UAV")
    await uav.action.arm()

    print("Taking Off")
    await uav.action.takeoff()


    await asyncio.sleep(10)

    print("LANDING")
    await uav.action.land()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())