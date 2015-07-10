#!/user/bin/env python
from reliable_serial import reliable_serial
from time import sleep

# Instructions
# ---------------------------------
# In the console, type lsusb to get information about your device. The result will be something like:
# "Bus 003 Device 004: ID 0403:6001 Future Technology Devices International, Ltd FT232 USB-Serial (UART) IC"
# The parameters to create a reliable_serial connection are as follows:
# VENID: The USB Vendor ID. This would be 0403 in the above example
# DEVID: The USB Device ID. This would be 6001 in the above example
# BAUD: The baud rate the device prefers. Default is 115200. Other common bauds include 9600 and 19200
# HEARTBEAT: Optional, a heartbeat character. Used to determine if the device is still responding. The recommended default is a \cr\lf character. Most devices respond with a \n
# HEARTBEAT_ACK: Optional, the expected response from a heartbeat command. The recommended default is a \n character. 
# HEARTBEAT_INTERVAL: Optional, the interval between heartbeats. Default is 1 second


# Parameters
# -----------------------------
# Insert these constants into your file
VENID = '0403'
DEVID = '6001'
BAUD = 115200
HEARTBEAT = 'loopback heartbeat'
HEARTBEAT_ACK = 'loopback heartbeat'
HEARTBEAT_INTERVAL = 5

#Use this constructor
#ser = reliable_serial(VENID, DEVID, BAUD) #No Heartbeat
ser = reliable_serial(VENID,DEVID,BAUD,HEARTBEAT,HEARTBEAT_ACK,HEARTBEAT_INTERVAL) #With heartbeat

ser.write("testdata\n");
response = ser.readline()
print response
if response == "testdata":
    print "Loopback Write and Read Succecss!"

response = ser.query("Knock knock",'\n',30)
if response == "Knock knock":
    print "Query Test Success!"


