def measureSWV():
    pass

# Standard library imports
import logging
import sys

# Local imports
import palmsens.instrument
import palmsens.mscript
import palmsens.serial


###############################################################################
# Start of configuration
###############################################################################

# COM port of the MethodSCRIPT device (None = auto-detect).
# In case auto-detection does not work or is not wanted, fill in the correct
# port name, e.g. 'COM6' on Windows, or '/dev/ttyUSB0' on Linux.
# DEVICE_PORT = 'COM6'
DEVICE_PORT = "/dev/ttyUSB0"

# Location of MethodSCRIPT file to use.
MSCRIPT_FILE_PATH = 'swv_settings.mscr'

###############################################################################
# End of configuration
###############################################################################


LOG = logging.getLogger(__name__)


def measure():
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

        # Read the script output (results) from the device.
        ec = 0
        while True:
            line = ""
            try :
                line = device.readline()
            except:
                print(line)
                pass
            # No data means timeout, so ignore it and try again.
            if not line:
                ec += 1
                print(ec)
                continue

            # An empty line means end of script.
            if line == '\n':
                break

            # Non-empty line received. Try to parse as data package.
            variables = palmsens.mscript.parse_mscript_data_package(line)

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
                print(' | '.join(cols))

if __name__ == "__main__":
    measure()