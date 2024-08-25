import subprocess
import re

def get_usb_ports():
    # Execute lsusb command to list USB devices
    lsusb_output = subprocess.check_output(['lsusb']).decode('utf-8')
    # print(lsusb_output)
    
    # Define the device names to search for
    devices = {
        "ESPicoDev": None,
        "FT230X Basic UART": None
    }
    
    # Search for the devices in the lsusb output
    for line in lsusb_output.split('\n'):
        for device_name in devices.keys():
            if device_name in line:
                # Extract the bus and device numbers
                match = re.search(r'Bus (\d+) Device (\d+):', line)
                if match:
                    bus = match.group(1)
                    device = match.group(2)
                    devices[device_name] = (bus, device)
    
    # Retrieve the corresponding ports using dmesg
    ports = {}
    dmesg_output = subprocess.check_output(['dmesg']).decode('utf-8')
    # print(dmesg_output)
    try:
        for device_name, (bus, device) in devices.items():
            if bus and device:
                # Search for the ttyUSB port in dmesg output
                match = re.search(r'ttyUSB\d+', dmesg_output)
                if match:
                    ports[device_name] = match.group(0)
    except TypeError:
        print("Devices are not connected")
    
    return ports

if __name__ == "__main__":
    ports = get_usb_ports()
    for device, port in ports.items():
        print(f"Device: {device}, Port: {port}")