# Standard library imports
import logging
import os
import sys
import csv
from datetime import datetime

# Local imports
import palmsens.instrument
import palmsens.mscript
import palmsens.serial


###############################################################################
# Start of configuration
###############################################################################

DEVICE_PORT = "/dev/ttyUSB0"

# Location of MethodSCRIPT file to use.
MSCRIPT_FILE_PATH = 'swv_settings.mscr' # 'swv_settings.mscr'

###############################################################################
# End of configuration
###############################################################################


LOG = logging.getLogger(__name__)

measurement_complete = False
meas_number = 0
file_dir = "results/"
file_header = "meas_"

def measure(meas_number):
    global measurement_complete
    """Run the example."""
    # Configure the logging.
    logging.basicConfig(level=logging.INFO, format='[%(module)s] %(message)s',
                        stream=sys.stdout)
    # Uncomment the following line to reduce the log level for our library.
    # logging.getLogger('palmsens').setLevel(logging.INFO)

    port = DEVICE_PORT
    if port is None:
        port = palmsens.serial.auto_detect_port()

    # Create and open serial connection to the device.
    LOG.info('Trying to connect to device using port %s...', port)
    with palmsens.serial.Serial(port, 5) as comm:
        device = palmsens.instrument.Instrument(comm)
        LOG.info('Connected.')

        # For development: abort any previous script and restore communication.
        device.abort_and_sync()

        # Check if device is connected and responding successfully.
        firmware_version = device.get_firmware_version()
        device_type = device.get_device_type()
        LOG.info('Connected to %s.', device_type)
        LOG.info('Firmware version: %s', firmware_version)
        LOG.info('MethodSCRIPT version: %s', device.get_mscript_version())
        LOG.info('Serial number = %s', device.get_serial_number())

        # Read MethodSCRIPT from file and send to device.
        device.send_script(MSCRIPT_FILE_PATH)
        os.makedirs(os.path.dirname(file_dir), exist_ok=True)

        # Read the script output (results) from the device. and write it into a CSV file\
        fname = file_dir + file_header + str(meas_number) + '.csv'
        with open(fname, 'w', newline='') as csvfile:
            
            csvwriter = csv.writer(csvfile)

            csvwriter.writerow(['Date and time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            csvwriter.writerow(['Notes', 'measurement' + str(meas_number)])
            # 3 rows to match header of the files created by the program. Usually contains information about the measurement.
            csvwriter.writerow([])
            csvwriter.writerow([])
            csvwriter.writerow([])

            csvwriter.writerow(['V', 'uA'])

            buffer = ""
            while True:
                data = ""
                try :
                    data = device.readline()
                except:
                    LOG.error("error reading from device")
                # No data means timeout, so ignore it and try again.
                if not data:
                    continue

                # An empty line means end of script.
                if data == '\n':
                    break

                variables = palmsens.mscript.parse_mscript_data_package(data)

                if variables:
                    # Apparently it was a data package. Print all variables.
                    cols = []
                    for var in variables:
                        cols.append(f'{var.type.name} = {var.value:11.4g} {var.type.unit}')
                        if 'status' in var.metadata:
                            status_text = palmsens.mscript.metadata_status_to_text(
                                var.metadata['status'])
                            cols.append(f'STATUS: {status_text:<16s}')
                        if 'cr' in var.metadata:
                            cr_text = palmsens.mscript.metadata_current_range_to_text(
                                device_type, var.type, var.metadata['cr'])
                            cols.append(f'CR: {cr_text}')
                    buffer += ' | '.join(cols) + '\n'


            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                print(line)

                if line == '':
                    break
                
                if 'Applied potential' in line and 'WE current' in line:
                    try:
                        potential = float(line.split('Applied potential =')[1].split('V')[0].strip())
                        current = float(line.split('WE current =')[1].split('A')[0].strip())
                        # Write values to CSV
                        current = str(float(current)*1000000)
                        csvwriter.writerow([potential, current])
                    except (IndexError, ValueError) as e:
                        LOG.error(f"Error parsing line: {line} - {e}")
    measurement_complete = True

if __name__ == "__main__":
    measure(meas_number)
    meas_number += 1