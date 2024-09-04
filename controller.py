# Needs 3 10K potentiometers on ADC0, AC1 and AC2
# Modified from Official Rasp Pi example here:
# https://github.com/micropython/micropython/tree/master/examples/bluetooth
# Tony Goodhew 23 June 2023

import bluetooth
import time
from typing import List

from machine import Pin
from joystick_channel import JoystickChannel




from ble_advertising import decode_services, decode_name

from micropython import const

lights: List[Pin]=[Pin(23, Pin.OUT), Pin(22, Pin.OUT), Pin(20, Pin.OUT), Pin(19, Pin.OUT)]

right_y = JoystickChannel(13)
left_y = JoystickChannel(34)
right_x = JoystickChannel(12)
left_x = JoystickChannel(35)
button_right = Pin(2, Pin.IN, Pin.PULL_DOWN)
button_left = Pin(21, Pin.IN, Pin.PULL_DOWN)
# End of additional code

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)

_UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX_CHAR_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX_CHAR_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")


class BLESimpleCentral:
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)

        self._reset()

    def _reset(self):
        # Cached name and address from a successful scan.
        self._name = None
        self._addr_type = None
        self._addr = None

        # Callbacks for completion of various operations.
        # These reset back to None after being invoked.
        self._scan_callback = None
        self._conn_callback = None
        self._read_callback = None

        # Persistent callback for when new data is notified from the device.
        self._notify_callback = None

        # Connected device.
        self._conn_handle = None
        self._start_handle = None
        self._end_handle = None
        self._tx_handle = None
        self._rx_handle = None

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND) and _UART_SERVICE_UUID in decode_services(
                adv_data
            ):
                # Found a potential device, remember it and stop scanning.
                self._addr_type = addr_type
                self._addr = bytes(
                    addr
                )  # Note: addr buffer is owned by caller so need to copy it.
                self._name = decode_name(adv_data) or "?"
                self._ble.gap_scan(None)

        elif event == _IRQ_SCAN_DONE:
            if self._scan_callback:
                if self._addr:
                    # Found a device during the scan (and the scan was explicitly stopped).
                    self._scan_callback(self._addr_type, self._addr, self._name)
                    self._scan_callback = None
                else:
                    # Scan timed out.
                    self._scan_callback(None, None, None)

        elif event == _IRQ_PERIPHERAL_CONNECT:
            # Connect successful.
            conn_handle, addr_type, addr = data
            if addr_type == self._addr_type and addr == self._addr:
                self._conn_handle = conn_handle
                self._ble.gattc_discover_services(self._conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Disconnect (either initiated by us or the remote end).
            conn_handle, _, _ = data
            if conn_handle == self._conn_handle:
                # If it was initiated by us, it'll already be reset.
                self._reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Connected device returned a service.
            conn_handle, start_handle, end_handle, uuid = data
            print("service", data)
            if conn_handle == self._conn_handle and uuid == _UART_SERVICE_UUID:
                self._start_handle, self._end_handle = start_handle, end_handle

        elif event == _IRQ_GATTC_SERVICE_DONE:
            # Service query complete.
            if self._start_handle and self._end_handle:
                self._ble.gattc_discover_characteristics(
                    self._conn_handle, self._start_handle, self._end_handle
                )
            else:
                print("Failed to find uart service.")

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Connected device returned a characteristic.
            conn_handle, def_handle, value_handle, properties, uuid = data
            if conn_handle == self._conn_handle and uuid == _UART_RX_CHAR_UUID:
                self._rx_handle = value_handle
            if conn_handle == self._conn_handle and uuid == _UART_TX_CHAR_UUID:
                self._tx_handle = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # Characteristic query complete.
            if self._tx_handle is not None and self._rx_handle is not None:
                # We've finished connecting and discovering device, fire the connect callback.
                if self._conn_callback:
                    self._conn_callback()
            else:
                print("Failed to find uart rx characteristic.")

        elif event == _IRQ_GATTC_WRITE_DONE:
            conn_handle, value_handle, status = data
            print("TX complete")

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            if conn_handle == self._conn_handle and value_handle == self._tx_handle:
                if self._notify_callback:
                    self._notify_callback(notify_data)

    # Returns true if we've successfully connected and discovered characteristics.
    def is_connected(self):
        return (
            self._conn_handle is not None
            and self._tx_handle is not None
            and self._rx_handle is not None
        )

    # Find a device advertising the environmental sensor service.
    def scan(self, callback=None):
        self._addr_type = None
        self._addr = None
        self._scan_callback = callback
        self._ble.gap_scan(2000, 30000, 30000)

    # Connect to the specified device (otherwise use cached address from a scan).
    def connect(self, addr_type=None, addr=None, callback=None):
        self._addr_type = addr_type or self._addr_type
        self._addr = addr or self._addr
        self._conn_callback = callback
        if self._addr_type is None or self._addr is None:
            return False
        self._ble.gap_connect(self._addr_type, self._addr)
        return True

    # Disconnect from current device.
    def disconnect(self):
        if self._conn_handle is None:
            return
        self._ble.gap_disconnect(self._conn_handle)
        self._reset()

    # Send data over the UART
    def write(self, v, response=False):
        if not self.is_connected():
            return
        self._ble.gattc_write(self._conn_handle, self._rx_handle, v, 1 if response else 0)

    # Set handler for when data is received over the UART.
    def on_notify(self, callback):
        self._notify_callback = callback

def bin_list_from_number(number: int, num_bits:int) -> List[bool]: #takes the device number and turns it into the requisite bits for the lights.
    binary_string = bin(number)[2:]
    binary_list = [char for char in binary_string]
    str_shortened_binary_list = binary_list[-num_bits:]
    return [bool(i) for i in str_shortened_binary_list]

def set_lights(list_values: List[bool]):
    for light, val in zip(lights, list_values):
        light.value(val)


ble = bluetooth.BLE()
central = BLESimpleCentral(ble)

not_found: bool = False

def on_scan(addr_type, addr, name):
    if addr_type is not None:
        print("Found peripheral:", addr_type, addr, name)
        central.connect()
    else:
        not_found = True
        print("No peripheral found.")


#this was the function I was in the middle of writing, to iterate thru all scanned peripherals, before I ran out of time. 
#def get_connected(): 
    



def demo(): # This is the MAIN LOOP
    




    central.scan(callback=on_scan)#start scanning for main boards to connect to. 

    with open("dev_name") as dev_name: #read the controller number
        raw_dev_number: str = dev_name.read()
    dev_number: int = int(raw_dev_number)
    # Wait for connection...
    while not central.is_connected():
        time.sleep_ms(100)
        if not_found:
            return

    print("Connected")

#    def on_rx(v):    # Not needed so commented out
#        print("RX", v)

#    central.on_notify(on_rx)
    
    with_response: bool = False
    tank_drive: bool = True
    binary_device_num: List[bool] = bin_list_from_number(dev_number, 4)
    set_lights(binary_device_num)
    looking_for_mode_swap: bool = False
    both_held_since = None    
    both_being_held: bool = False
    wait_until_not_held: bool = False
    doing_animation: bool = False
    lights_dirty: bool = False
    animation_index: int = 0
    last_animation_time: int = 0

    #animations are stored with [tank_mode][animation_index]
    animations: List[List[List[bool]]] = [[[False,True,True,False],
                                          [True,False,False,True],
                                          [False,True,True,False],
                                          [True,False,False,True],
                                          [False,True,True,False],
                                          [True,False,False,True],
                                          [False,True,True,False],
                                          [True,False,False,True],],
                                          [[True,False,False,True],
                                           [False,True,True,False],
                                           [True,False,False,True],
                                           [False,True,True,False],
                                           [True,False,False,True],
                                           [False,True,True,False],
                                           [True,False,False,True],
                                           [False,True,True,False],]]



    while central.is_connected():
        if button_left.value() and button_right.value():   
            if not wait_until_not_held:
                if not both_being_held: #is this the start of a push?
                    both_being_held = True #remember that we've started pushing the button
                    both_held_since = time.ticks_ms() #record that we've stopped pushing the button
                elif time.ticks_diff(time.ticks_ms(), both_held_since) > 1500:
                    tank_drive = not tank_drive
                    wait_until_not_held = True
                    doing_animation = True
                    animation_index = 0
                    lights_dirty = True
        else:
            both_being_held = False
            wait_until_not_held = False
        
        if lights_dirty: #animation handling code. 
            if not doing_animation:
                set_lights(binary_device_num)
                lights_dirty = False
            else: #we are doing an animation
                if animation_index == 0:
                    set_lights(animations[tank_drive][animation_index])
                    animation_index += 1
                    last_animation_time = time.ticks_ms()
                else:
                    if time.ticks_diff(time.ticks_ms(), last_animation_time) > 500:
                        animation_index+=1
                        if animation_index == len(animations[tank_drive]):
                            doing_animation = False
                        else:
                            set_lights(animations[tank_drive][animation_index])
                            last_animation_time = time.ticks_ms()
        if tank_drive:
            v = f"{left_y.get_pow()},{right_y.get_pow()},{button_left.value()},{button_right.value()},{dev_number}\n"
        else:
            v = f"{left_y.get_pow() - left_x.get_pow()},{left_y.get_pow() + left_x.get_pow()},{button_left.value()},{button_right.value()},{dev_number}\n"
        print(v)
        try:
            

            central.write(v, with_response)
        except:
            print("TX failed")
        time.sleep_ms(400 if with_response else 30)

    print("Disconnected")
# End of modification for ADC control

if __name__ == "__main__":
    demo()

