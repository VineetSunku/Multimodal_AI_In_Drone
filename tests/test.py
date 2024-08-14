from dronekit import connect
import time
import argparse

def connectMyCopter(conn_str):
    if not conn_str:
        import dronekit_sitl
        sitl = dronekit_sitl.start_default()
        conn_str = sitl.connection_string()
    vehicle = connect(conn_str, wait_ready=True)

    return vehicle


def get_arguments():
    parser = argparse.ArgumentParser(description='commands')
    parser.add_argument('--connect')
    args = parser.parse_args()

    return args


def prepare_vehicle_for_flight(vehicle):
    print('Waiting for SITL vehicle to finish initialising...')
    time.sleep(5)

    while not vehicle.is_armable:
        print('Waiting for the vehicle to become armable')
        time.sleep(1)
    print('Vehicle is now armable')

    # Set the vehicle to guided mode
    print('Vehicle is in %s mode'%vehicle.mode)
    #vehicle.mode = VehicleMode("GUIDED")
    vehicle.mode = 'GUIDED'
    while vehicle.mode != 'GUIDED':
        print('Vehicle is in %s mode'%vehicle.mode)
        print('Last heartbeat:%s'%vehicle.last_heartbeat)
        print('Status: %s'%vehicle.system_status)
        print('Waiting for the vehicle to enter GUIDED flight mode')
        time.sleep(1)
    print('Vehicle is now in guided mode')

    #Arm the drone
    vehicle.armed = True
    while not vehicle.armed:
        print('Waiting for the vehicle to become armed')
        print('Last heartbeat:%s'%vehicle.last_heartbeat)
        print('Status: %s'%vehicle.system_status)
        print('Armed: %s'%vehicle.armed)
        time.sleep(1)
    print('Virtual propellers are now spinning!')


def set_and_get_params(vehicle):
    gps_type = vehicle.parameters['GPS_TYPE']
    print('GPS type: %s'%gps_type)
    vehicle.parameters['GPS_TYPE'] = 3
    gps_type = vehicle.parameters['GPS_TYPE']
    print('GPS type: %s'%gps_type)


def arm_and_take_off(vehicle, targetHeight):
    prepare_vehicle_for_flight(vehicle)
    vehicle.simple_takeoff(targetHeight)
    print('Taking off...')

    while vehicle.location.global_relative_frame.alt < 0.95*targetHeight:
        print('Current altitude: %d'%vehicle.location.global_relative_frame.alt)
        time.sleep(1)
    print('Target altitude reached!')


def main():
    args = get_arguments()
    vehicle = connectMyCopter(args.connect)
    arm_and_take_off(vehicle, 10)
    
    # Script logic goes here. Preferably a function call.



    vehicle.close()



if __name__ == '__main__':
    main()