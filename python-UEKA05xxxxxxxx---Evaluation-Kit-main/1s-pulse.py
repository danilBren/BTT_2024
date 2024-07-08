"""
Turn the pump on at 1W for 1 second, then turn it off
"""

import serial
import time

# set up port – replace COM port number with the COM port you are using
serial_port = serial.Serial(port="COM30",
                            baudrate=115200,
                            bytesize=8,
                            timeout=2,
                            stopbits=serial.STOPBITS_ONE)

# turn off data streaming mode
serial_port.write(b"#W2,0\n")

# turn the pump off whilst configuring system
serial_port.write(b"#W0,0\n")

# set the pump to manual control mode
serial_port.write(b"#W10,0\n")

# set the drive power input to register 23
serial_port.write(b"#W11,0\n")

# set the drive power set point to 1000 mW
serial_port.write(b"#W23,1000\n")

# turn the pump on
serial_port.write(b"#W0,1\n")

# wait for 1 second
time.sleep(1)

# turn the pump off
serial_port.write(b"#W0,0\n")

# close serial port
serial_port.close()
