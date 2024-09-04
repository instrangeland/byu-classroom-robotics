from machine import ADC
class JoystickChannel:
    def __init__(self, pin:int) -> None:
        self.adc = ADC(pin, atten=ADC.ATTN_11DB)
        self.max: int = 0 #maximum value we've seen from the joystick, so we can get a good sense of what percentage the joystick is at
        self.min: int = 2450000 #same but for minimum
        self.center: int = self.adc.read_uv() #we figure it will prob be in the center when we start
    
    def get_pow(self) -> float:
        val: float = self.adc.read_uv() # for the esp-32, this function gives a voltage level. It is calibrated in factory
        if val > self.max: # Check if the current is a higher/lower value than we've ever seen. 
            self.max = val
        if val < self.min:
            self.min = val
        dif = self.max - self.min + .001 #we add .001, since until the person starts moving the joysticks, 
        #we've now set the minimum and maximum values to the same value, we don't wanna divide by 0
        if not dif == 0: #just in case divide by 0 check. 
            return (val - self.center) / dif * 2
        elif abs(val-self.center)/dif < .08
            return 0
        return 0
