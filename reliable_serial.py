#!/user/bin/env python
import serial
import threading
import usb
from time import sleep
from usbid.device import device_list

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
#
# Example usage:
# foo = reliable_serial('0403','6001',115200,'\r','\n',5)


class reliable_serial(object):

    #Constants and Defaults
    MAX_DEVICE_ADDR = 5 #largest tty device we check
    DEFAULT_HEARTBEAT_DELAY = 1 #Time between heartbeats in seconds
    AUTOCONNECT_DELAY = 1 #Time between autoconnect tries
    DEFAULT_TIMEOUT = .25 #pyserial timeout
    DEFAULT_QUERY_TIMEOUT_MS = 30 #milliseconds to wait for device to respond with query response
    DEFAULT_BAUDRATE = 115200
    DEFAULT_CARRIAGE_RETURN = '\r'
    DEFAULT_BAUDRATE = 115200

    #Instance Variables
    ser = None
    heartbeat_phrase = None
    heartbeat_response = None
    heatbeat_delay = None
    scheduled = False
    vendorID = None
    productID = None
    
    def __init__(self,vendorID,productID, baudrate = DEFAULT_BAUDRATE, heartbeat_phrase = None, heartbeat_response = None, heartbeat_delay = None):
        
        #Initialize
        self.lock = threading.Lock()
        self.timer = None
        self.vendorID = vendorID
        self.productID = productID
        self.baudrate = baudrate
        self.heartbeat_phrase = heartbeat_phrase
        self.heartbeat_response = heartbeat_response
        self.heartbeat_delay = heartbeat_delay

        #Begin autoconnection
        self.__autoconnect()

        #Begin heartbeat if requested
        if heartbeat_phrase != None:
            self.__heartbeat()

    def __find_handle(self, vendorID, productID):
        ttys = [_ for _ in device_list() if  _.tty]
        for dev in ttys:
            if dev.idVendor == vendorID and dev.idProduct == productID:
                return ("/dev/" + dev.tty), dev.nameVendor + " " + dev.nameProduct
        return None, None;

    def __schedule_autoconnect(self):
            if self.scheduled == False:
                self.scheduled = True
                self.timer = threading.Timer(self.AUTOCONNECT_DELAY,self.__autoconnect).start()

    def __autoconnect(self):
        path, human_name = self.__find_handle(self.vendorID, self.productID)
        if path is not None:
            try:
                self.lock.acquire()
                self.ser = serial.Serial(port = path, baudrate = self.baudrate, timeout = self.DEFAULT_TIMEOUT)
                print "reliable serial: successfully connected to " + human_name
            except serial.SerialException as detail:
                print "reliable_serial: can't connect to device: " , detail
                self.__schedule_autoconnect()
            except TypeError as detail:
                print "reliable_serial: can't connect to device: " , detail
                self.__schedule_autoconnect()
                self.ser.close()
            except ValueError as detail:
                print "reliable_serial: can't connect to device: " , detail
                self.__schedule_autoconnect()
            except IOError as detail:
                print "reliable_serial: can't connect to device: " , detail
                self.__schedule_autoconnect()
            finally:
                self.scheduled = False
                self.lock.release()
        else:
            print "reliable_serial: no USB device found at " + self.vendorID + ":" + self.productID
            self.lock.acquire()
            self.scheduled = False
            self.__schedule_autoconnect()
            self.lock.release()

    def __heartbeat(self):
            if self.ser is not None:
                response = self.query(self.heartbeat_phrase)
                if response is None:
                    self.ser.close()
                    self.ser = None;
                else:
                    if(response != self.heartbeat_response):
                        self.ser.close()
                        self.ser = None;
                    else:
                        pass;
            threading.Timer(self.heartbeat_delay,self.__heartbeat).start()

    # Query
    # ------------------------------------------------------------------------------------------------------
    # Aggressively sends a command and wait for a response. Flushes input and output buffers and is blocking.
    # Assumes that the device being queried uses a standard EOL character.
    def query(self,query, eol = '\n', timeout = DEFAULT_QUERY_TIMEOUT_MS):
        self.lock.acquire()
        try:
            if(self.ser != None):
                self.ser.getDSR() #raises an exception if error results
                self.ser.flushInput()
                self.ser.flushOutput()
                self.ser.write(query + eol)
                sleep(timeout/1000.)
                response = self.ser.readline()
                self.ser.flushInput()
                self.ser.flushOutput()
                return response.strip()
            else:
                return None
        except (serial.SerialException,IOError, ValueError):
            if self.scheduled == False:
                print "reliable_serial: device query error, attempting to autoconnect"
                self.__schedule_autoconnect()
            return None;
        finally:
            self.lock.release()

    # Write
    # ------------------------------------------------------------------------------
    # Send a command over the serial interface. Does not add any terminating characters
    def write(self,data):
        self.lock.acquire()
        try:
            if(self.ser != None):
                self.ser.getDSR() #attempts to read a deprecated part of the serial interface...throws an exception if no serial device is present
                self.ser.write(data)
            else:
                return None
        except (serial.SerialException,IOError, ValueError):
            if self.scheduled == False:
                print "reliable_serial: device write error, attempting to autoconnect"
                self.__schedule_autoconnect()
            return None;
        finally:
            self.lock.release()

    # read
    # -----------------------------------------------------
    # Error-handling version of the pyserial 'read' command.
    # Reads a specified number of bytes. Default read size is 1
    def read(self, size = 1): 
        self.lock.acquire()
        try:
            if(self.ser != None):
                self.ser.getDSR() #attempts to read a deprecated part of the serial interface...throws an exception if no serial device is present
                response = self.ser.read(size)
                return response
            else:
                return None
        except (serial.SerialException,IOError, ValueError):
            print "reliable_serial: device read error, attempting to autoconnect"
            self.__schedule_autoconnect()
            return None;
        finally:
            self.lock.release()

    # readline 
    # ----------------------------------------------------------
    # Error-handling version of the pyserial 'readline' function. 
    # Reads until a '\n' character is reached.
    def readline(self, size = None): 
        self.lock.acquire()
        try:
            if(self.ser != None):
                self.ser.getDSR() #attempts to read a deprecated part of the serial syntax...throws an exception if no serial device is present
                response = self.ser.readline(size)
                return response.strip()
            else:
                return None
        except (serial.SerialException,IOError, ValueError):
            print "reliable_serial: device read error, attempting to autoconnect"
            self.__schedule_autoconnect()
            return None;
        finally:
            self.lock.release()
    # close
    # -------------
    # Call close to close the connection and freee memory
    def close(self):
        if self.ser != None:
            self.ser.close();

    def __del__(self):
        if self.ser != None:
            self.ser.close();

