import asyncio
import random
from mavsdk import System
from pynput.keyboard import Key, Listener  # Replacing KeyPressModule with pynput

# Drone control parameters
roll, pitch, throttle, yaw = 0, 0, 0.5, 0
uav = System()

# Keyboard listener to capture key presses
def on_press(key):
    global roll, pitch, throttle, yaw
    value = 1
    if key.char == "a":
        yaw = -value
    elif key.char == "d":
        yaw = value
    elif key.char == "w":
        throttle = value
    elif key.char == "s":
        throttle = 0
    elif key.char == "i":
        asyncio.ensure_future(print_flight_mode(uav))
    elif key.char == "q":
        asyncio.ensure_future(arm_drone(uav))
    elif key.char == "l":
        asyncio.ensure_future(land_drone(uav))

# def on_release(key):
#     global roll, pitch, throttle, yaw
#     roll, pitch, throttle, yaw = 0, 0, 0.5, 0

async def print_flight_mode(my_drone):
    async for flight_mode in my_drone.telemetry.flight_mode():
        print("FlightMode:", flight_mode)
        break  # Stop after printing the current flight mode

async def arm_drone(my_drone):
    if await my_drone.telemetry.landed_state() == my_drone.telemetry.LandedState.ON_GROUND:
        await my_drone.action.arm()
        print("Drone armed")

async def land_drone(my_drone):
    if await my_drone.telemetry.in_air():
        await my_drone.action.land()
        print("Drone landing")

async def manual_control_drone(my_drone):
    global roll, pitch, throttle, yaw
    while True:
        print(f"Control Input: Roll: {roll}, Pitch: {pitch}, Throttle: {throttle}, Yaw: {yaw}")
        await my_drone.manual_control.set_manual_control_input(roll, pitch, throttle, yaw)
        await asyncio.sleep(0.1)

async def run_uav():
    await uav.connect(system_address="udp://:14540")
    print("Waiting for drone to connect...")
    async for state in uav.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    async for health in uav.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position state is good enough for flying.")
            break

    asyncio.ensure_future(manual_control_drone(uav))

async def run():
    """Main function to connect to the drone and input manual controls"""
    await run_uav()

if __name__ == "__main__":
    # Start the keyboard listener

    # Start the main function
    asyncio.ensure_future(run())

    # Runs the event loop until the program is canceled with e.g., CTRL-C
    asyncio.get_event_loop().run_forever()
    
    with Listener(on_press = on_press) as listener:   
        listener.join()
