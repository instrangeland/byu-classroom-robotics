# BYU Classroom Robotics

## Introduction

Welcome to the **BYU Classroom Robotics** project. It was built for the as a 2024 Immerse Broader Impacts Project by Ethan Hunter and Ephraim.

It utelizes a Rpi Pico for the main board and ESP32s for the controllers. Many features should move over to any other micropython based board, though the actual boards would need redesign. 

Most of the files are not used in the actual robots! They are simply there as documenting the journey, and maybe helping give some basic examples for how to use some of the libraries. 

The two you'll want to look at is main.py, for the main board and controller.py. Each board will also need to have ble_advertising.py copied to the board. The joystick will need joystick_channel.py as well. 

The controller allows switching between tank drive & one joystick driving. The default is tank drive. It displays an animation when switching on the controller. 

Each controller must be assigned a number. Make sure to put a file called "dev_name" with the number on the flash as well. When the controller and the robot connect, they will both light up the controller number in binary on the included LEDs.

The pairing is only... partially done. There's a few options I see for it now. Currently, the pairing code only really allows for one controller + one robot. I never got around to rewriting the bluetooth scan code for it to find a list of all bluetooth devices and than iterate thru them. The way I see it working is that the main board is constantly advertising how many connections it has. The controllers will cycle thru all available connections. When it connects to one, it checks to see if it has 1 or 0 connections. Then it waits a random amount of time, and then if it still says it's only connected to one, it "locks in." If another one is connected after that time, it flips a coin, 25% it switches. If it doesn't switch, it waits a random amount of time, and then switches again. Overall, they should all find their own connections eventually. It is already set up to transmit the controller number, and the main board transmits how many devices are connected. 

The main board uses a seperate smaller board for the LEDs. The controller has them built in. 
