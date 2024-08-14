# from mavsdk import System
# import asyncio
# import math
# import time
# import argparse
# from DroneLogger import log
# from basicMoves import *

# ######### GLOBAL CONSTANTS #########

# # Earth radius in meters
# EARTH_RADIUS = 6378137.0
    
# ######### BASIC MOVEMENTS #########
# # Arm and Takeoff
# async def arm_and_takeoff(alt):
#     if not await isArmed():
#         log.warn("UAV is not yet armed! Arming UAV...")
#         await uav.action.arm()
#     log.info("UAV is armed")
#     log.debug("Setting Takeoff altitude")
#     await uav.action.set_takeoff_altitude(altitude=alt)
#     log.info("Taking Off")
#     await uav.action.takeoff()
#     await asyncio.sleep(10)  # Wait for 10 seconds to stabilize
    

# # Hover
# async def hover( duration):
#     log.info(f"Hovering for {duration} seconds")
#     await asyncio.sleep(duration)

# # Land UAV
# async def land_uav():
#     log.info("LANDING")
#     await uav.action.land()

# # Move Right
# async def move_right(distance_m):
#     current_lat, current_lon, current_alt = await get_coord()

#     delta_lon = (distance_m / EARTH_RADIUS) * (180 / math.pi) / math.cos(current_lat * math.pi / 180)
#     new_lon = current_lon + delta_lon

#     await uav.action.goto_location(current_lat, new_lon, current_alt, current_alt)
#     log.info(f"Moved {distance_m} meters right to new location: Latitude: {current_lat}, Longitude: {new_lon}, Altitude: {current_alt}")

# # Move Left
# async def move_left( distance_m):
#     current_lat, current_lon, current_alt = await get_coord()

#     delta_lon = (distance_m / EARTH_RADIUS) * (180 / math.pi) / math.cos(current_lat * math.pi / 180)
#     new_lon = current_lon - delta_lon

#     await uav.action.goto_location(current_lat, new_lon, current_alt, current_alt)
#     log.info(f"Moved {distance_m} meters left to new location: Latitude: {current_lat}, Longitude: {new_lon}, Altitude: {current_alt}")

# # Move Forward
# async def move_forward( distance_m):
#     current_lat, current_lon, current_alt = await get_coord()

#     delta_lat = (distance_m / EARTH_RADIUS) * (180 / math.pi)
#     new_lat = current_lat + delta_lat

#     await uav.action.goto_location(new_lat, current_lon, current_alt, current_alt)
#     log.info(f"Moved {distance_m} meters forward to new location: Latitude: {new_lat}, Longitude: {current_lon}, Altitude: {current_alt}")

# # Move Backward
# async def move_backward(distance_m):
#     current_lat, current_lon, current_alt = await get_coord()

#     delta_lat = (distance_m / EARTH_RADIUS) * (180 / math.pi)
#     new_lat = current_lat - delta_lat

#     await uav.action.goto_location(new_lat, current_lon, current_alt, current_alt)
#     log.info(f"Moved {distance_m} meters backward to new location: Latitude: {new_lat}, Longitude: {current_lon}, Altitude: {current_alt}")

# # Move Up
# async def move_up( distance_m):
#     current_lat, current_lon, current_alt = await get_coord()

#     new_alt = current_alt + distance_m

#     await uav.action.goto_location(current_lat, current_lon, new_alt, new_alt)
#     log.info(f"Moved {distance_m} meters up to new location: Latitude: {current_lat}, Longitude: {current_lon}, Altitude: {new_alt}")

# # Move Down
# async def move_down( distance_m):
#     current_lat, current_lon, current_alt = await get_coord()

#     new_alt = current_alt - distance_m

#     await uav.action.goto_location(current_lat, current_lon, new_alt, new_alt)
#     log.info(f"Moved {distance_m} meters down to new location: Latitude: {current_lat}, Longitude: {current_lon}, Altitude: {new_alt}")

# # Move to Custom Location
# async def move_to_location( x, y, z):
#     log.info(f"Moving to location ({x}, {y}, {z})")
#     await uav.action.goto_location(x, y, z, 0)
