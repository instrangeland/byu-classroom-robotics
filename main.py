import bluetooth
import random
import struct
import time
from ble_advertising import advertising_payload
from micropython import const
from machine import PWM, Pin
from collections import deque
from typing import List
import machine
import rp2

## Main board control program
## By Ethan Hunter

ir_receiver = machine.Pin(0, machine.Pin.IN)
ir_transmit = machine.Pin(1, machine.Pin.OUT)

## from here to the next comment is copied from 
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

button_bluetooth = Pin(11, Pin.IN, Pin.PULL_DOWN)

class BLESimplePeripheral:
    def __init__(self, ble, name="mpy-uart"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback

hit_type = deque(tuple([0] * 10), 10)
time_hit = deque(tuple([0] * 10), 10)

def got_hit(pin):
    time_hit_var = time.ticks_us()
    ir_val = ir_receiver.value()
    time_hit.append(time_hit_var)
    hit_type.append(ir_val)
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def fire():
    set(x, 60)
    label("delay_high_1")
    set(pins, 1)
    nop()
    set(pins, 0)
    jmp(x_dec, "delay_high_1")
    set(x, 30)
    label("delay_low_1")
    set(pins, 0)
    nop()
    set(pins, 0)
    jmp(x_dec, "delay_low_1")
    set(x, 30)
    label("delay_high_2")
    set(pins, 1)
    nop()
    set(pins, 0)
    jmp(x_dec, "delay_high_2")
    set(x, 30)
    label("delay_low_2")
    set(pins, 0)
    nop()
    set(pins, 0)
    jmp(x_dec, "delay_low_2")
    
def bin_list_from_number(number: int, num_bits:int) -> List[bool]: #takes the device number and turns it into the requisite bits for the lights.
    binary_string = bin(number)[2:]
    binary_list = [char for char in binary_string]
    str_shortened_binary_list = binary_list[-num_bits:]
    return [bool(i) for i in str_shortened_binary_list]

def set_lights(list_values: List[bool]):
    for light, val in zip(lights, list_values):
        light.value(val)

rp2.PIO(0).remove_program()
sm = rp2.StateMachine(0, fire, freq=152000, set_base=Pin(1))
sm.active(1)
sm.active(0)
# This is the MAIN LOOP
def demo():    # This part modified to control Neopixel strip
    #uncommment these!!!
    ble = bluetooth.BLE()
    p = BLESimplePeripheral(ble)
    right_motor_back = PWM(Pin(13))
    right_motor_fwd = PWM(Pin(12))
    left_motor_back = PWM(Pin(10))
    left_motor_fwd = PWM(Pin(11))
    right_motor_back.freq(1000)
    right_motor_fwd.freq(1000)
    left_motor_back.freq(1000)
    left_motor_fwd.freq(1000)

    def on_rx(v):  # v is what has been received
        try:
            val = str(v)
            val = val[2:-3]
            parts = val.split(",")
            print(parts)
            left_power = float(parts[0])
            right_power = float(parts[1])
            left_button = int(parts[2])
            if left_power>.1:
                left_motor_fwd.duty_u16(int(65535*left_power))
                left_motor_back.duty_u16(0)
            elif left_power < -.1:
                left_motor_back.duty_u16(int(-65535*left_power))
                left_motor_fwd.duty_u16(0)
            else:
                left_motor_back.duty_u16(0)
                left_motor_fwd.duty_u16(0)
            if right_power>.1:
                print("ritefwd")
                right_motor_fwd.duty_u16(int(65535*right_power))
                right_motor_back.duty_u16(0)
            elif right_power < -.1:
                print("riteback")
                right_motor_back.duty_u16(int(-65535*right_power))
                right_motor_fwd.duty_u16(0)
            else:
                right_motor_back.duty_u16(0)
                right_motor_fwd.duty_u16(0)
        except:
            print("something went wrong, skipping")

        
        
    #| Pin.IRQ_FALLING
    #p.on_write(on_rx)
    ir_receiver.irq(trigger=Pin.IRQ_RISING , handler=got_hit)
    hits_in_a_row = 0
    life = 8
    last_hit_time = time.ticks_ms()
    while True:
        sm.active(1)
        code = []
        p.send(f"{len(p._connections)}\n")
        if not last_hit_time + 1500 > time.ticks_ms():
            if len(hit_type) >= 2:
                first_time = time_hit.popleft()
                time_length = time.ticks_diff(time_hit.popleft(), first_time)
                init_val = hit_type.popleft()
                final_val = hit_type.popleft()
                print(f"time: {time_length} initial: {init_val} final: {final_val}")
                if time_length > 1400 and time_length < 1700:
                    hits_in_a_row +=1
                else:
                    hits_in_a_row = 0
            if hits_in_a_row > 4:
                print("got hit!!!")
                hits_in_a_row = 0
                life -= 1
                last_hit_time = time.ticks_ms()
        
        else:
            time.sleep(.1)
            
            


if __name__ == "__main__":
    demo()
