import logging

######### SETUP LOGGING #########
formatter = logging.Formatter(fmt='[%(levelname)s]: %(asctime)s:%(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Log Handler to print to logs
file_handler = logging.FileHandler('./logs/DroneMovements.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create a stream handler to print logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(console_handler)