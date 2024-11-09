import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError


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
        
    i=0
    async for health in uav.telemetry.health():
        print(health)
        i+=1
        if health.is_armable or i==5:
            break
        await asyncio.sleep(1)
        
    
    print("Arming the uav...")
    await uav.action.arm_force()

    # Wait for 3 seconds
    await asyncio.sleep(3)
    
    print("Setting initial setpoints...")
    await uav.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, 0.0, 0.0, 0.0))  

    print("Starting offboard control...")
    try:
        await uav.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: {error}")
        print("-- Disarming")
        await uav.action.disarm()
        return

    print("Taking off manually...")
    await uav.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, 0.0, -1.0, 0.0))  # Ascend with -1.0 m/s velocity

    await asyncio.sleep(3)

    print("Hovering...")
    await uav.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, 0.0, 0.0, 0.0))  # Hover in place

    await asyncio.sleep(10)

    print("Landing manually...")
    await uav.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, 0.0, 1.0, 0.0))  # Descend with 1.0 m/s velocity

    await asyncio.sleep(3)

    print("Stopping offboard control...")
    try:
        await uav.offboard.stop()
    except OffboardError as error:
        print(f"Stopping offboard mode failed with error code: {error._result.result}")

    print("Disarming...")
    await uav.action.disarm()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())