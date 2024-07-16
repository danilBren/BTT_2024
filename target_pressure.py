"""
Setup a PID loop to control to pressure, and set a target pressure.
"""

import serial
import time

# set up port – replace COM port number with the COM port you are using
pump_port = serial.Serial(port="/dev/ttyUSB0",
                            baudrate=115200,
                            bytesize=8,
                            timeout=2,
                            stopbits=serial.STOPBITS_ONE)

# turn off data streaming mode
pump_port.write(b"#W2,0\n")

# turn the pump off whilst configuring system
pump_port.write(b"#W0,0\n")

# set the pump to PID control mode
pump_port.write(b"#W10,1\n")

# set the PID setpoint to register 23
pump_port.write(b"#W12,0\n")

# set the PID input to the pressure sensor (analog input 2)
pump_port.write(b"#W13,2\n")

# set the PID proportional coefficient to 50
pump_port.write(b"#W14,10\n")

# set the PID integral coefficient to 100
pump_port.write(b"#W15,10\n")

# set the target pressure
pump_port.write(b"#W23,20\n")

# turn the pump on
pump_port.write(b"#W0,1\n")

# close serial port
pump_port.close()