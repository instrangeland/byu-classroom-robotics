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

while True:
    print(f"r_y: {right_y.get_pow()}")
    print(f"l_y: {left_y.get_pow()}")
    sleep(.25)

#13- right y
#12- right x
