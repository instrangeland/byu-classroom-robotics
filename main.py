from machine import Pin, PWM
from time import sleep
from micropython import const
from collections import deque
from alternateble import BLUART
import bluetooth
import struct

NUM_LIGHTS = const(4)

class IndicatorLights:
    def __init__(self, pinNums):
        self.pins = []W
        for pinNum in pinNums:
            self.pins.append(Pin(pinNum, Pin.OUT))
    
    def setPins(self, pinsValue):
        for pin, pinValue in zip(self.pins, pinsValue):
            pin.value(pinValue)

            
        
        
    
def printToUART(string, uart):
    bytesVal = struct.pack("<s",string)
    uart.write(bytesVal)
            
    

class MotorNoPWM:
    def __init__(self, fwdPin: int, bckPin: int):
        self.fwd = Pin(fwdPin, Pin.OUT)
        self.bck = Pin(bckPin, Pin.OUT)
        
    def forward(self):
        self.fwd.value(0)
        self.bck.value(1)
        
    def backward(self):
        self.fwd.value(1)
        self.bck.value(0)
    def stop(self):
        self.fwd.value(0)
        self.bck.value(0)
    

class Motor:
    def __init__(self, fwdPin: int, bckPin: int):
        self.fwdPWM = PWM(Pin(fwdPin, Pin.OUT))
        self.bckPWM = PWM(Pin(bckPin, Pin.OUT))
        self.fwdPWM.freq(500)
        self.bckPWM.freq(500)
        
    
    def forward(self,amount: int):
        self.bckPWM.duty_u16(0)
        self.fwdPWM.duty_u16(min(65535,amount))
        
    def backward(self,amount: int):
        self.fwdPWM.duty_u16(0)
        self.bckPWM.duty_u16(min(65535,amount))
    def stop(self):
        self.fwdPWM.duty_u16(0)
        self.bckPWM.duty_u16(0)
        
leftMotor = MotorNoPWM(28,27)
rightMotor = MotorNoPWM(26,22)

lights = IndicatorLights([16,17,18,19])

def iterList(list):
    index = 0
    while True:
        print(list)
        list[index]+=1
        if list[index] > 1:
            list[index] = 0
        else:
            break
        index+=1
        if index > 3:
            break
    return list

lights.setPins([0,0,0,0])
lightList = [0,0,0,0]

ble = bluetooth.BLE()
myUART = BLUART(ble)
while True:
    toParse = deque([], 15)
    def on_rx():
        toParse.append(myUART.read().decode().strip())
    myUART.irq(handler=on_rx)
    
    while True:
        if len(toParse)>0:
            val = toParse.popleft()
            splitList = val.split()
            if splitList[0] == "on":
                print("turned on "+splitList[1])
                myUART.write("turned on "+splitList[1]+"\n")
                lights.pins[int(splitList[1])].value(1)
            elif splitList[0] == "off":
                myUART.write("turned off "+splitList[1]+"\n")
                print("turned off "+splitList[1])
                lights.pins[int(splitList[1])].value(0)
            elif splitList[0] == "fwd":
                myUART.write("going fwd\n")
                leftMotor.forward()
                rightMotor.forward()
            elif splitList[0] == "stop":
                myUART.write("going fwd\n")
                leftMotor.stop()
                rightMotor.stop()
            elif splitList[0] == "bwd":
                myUART.write("going bwd\n")
                leftMotor.backward()
                rightMotor.backward()
            elif splitList[0] == "try":
                myUART.write("going bwd\n")
                leftMotor.backward()
                rightMotor.backward()
            elif splitList[0] == "left":
                myUART.write("going bwd\n")
                leftMotor.backward()
                rightMotor.forward()
            elif splitList[0] == "right":
                myUART.write("going bwd\n")
                leftMotor.forward()
                rightMotor.backward()
            elif splitList[0] == "lonly":
                myUART.write("going bwd\n")
                leftMotor.forward()
                rightMotor.stop()
            elif splitList[0] == "ronly":
                myUART.write("going bwd\n")
                leftMotor.stop()
                rightMotor.forward()
            else:
                print(splitList[0])
                print(len(splitList[0]))

                  
            
            
            
        
    
    






