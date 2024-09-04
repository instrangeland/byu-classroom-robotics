from time import sleep_ms
import time
from bleradio import BLERadio
from machine import Timer
from machine import ADC
from machine import Pin
from joystick_channel import JoystickChannel
from time import sleep
# right_x = ADC(12, atten=ADC.ATTN_11DB)
# right_y = ADC(13, atten=ADC.ATTN_11DB)
# button_right = Pin(2, Pin.IN, Pin.PULL_DOWN)
# button_left = Pin(21, Pin.IN, Pin.PULL_DOWN)
# left_x = ADC(35, atten=ADC.ATTN_11DB)
# left_y = ADC(34, atten=ADC.ATTN_11DB)

right_y = JoystickChannel(13)
left_y = JoystickChannel(34)
button_right = Pin(2, Pin.IN, Pin.PULL_DOWN)
button_left = Pin(21, Pin.IN, Pin.PULL_DOWN)


radio = BLERadio(broadcast_channel=5)

leftpower = 0
rightpower = 0

start = time.ticks_ms()



#left_power, left_power_velocity, right_power, right_power_velocity, left_button, right_button
def transmit(left_power, right_power, left_button, right_button):
    radio.broadcast([left_y.get_pow(), right_y.get_pow(), button_left.value(), button_right.value()])

def read_trans():
    pass
    #transmit(, right_y.get_pow(), button_left.value(), button_right.value())

