# Python Slot Car Lap Timer
A Python3 based slot car lap timer dashboard built with Tkinter.

This is a an ongoing extension / attempt for generalization of the Raspberry Pi 3b project from @philm400. Also I did not manage to fully complete this yet. Hopefully I can collaborate with @philm400 or you, dear reader, to finish this later.

Some changes to this version:
* Support for 4 lanes (instead of just two).
* Uses Arduino that sends "1" "2" "3" "4" over serial to signal passing cars.
* Better support for multiple screen sizes.
* Audio comes from PC, not from a buzzer.

The basis of the timer is derived from: http://code.activestate.com/recipes/578666-stopwatch-with-laps-in-tkinter

### Pre-requisities:
* Reaspberry Pi *OR a PC*
* Arduino or compatible
* Breadboard or soldering iron
* Some wires
* 1KΩ and 10KΩ resistors
* Reed sensors - Sealed / pre-wired ones are best like these: http://ebay.eu/2kwWhZ7
* Python3
* Tkinter Library installed
* Slot car track
* Slot cars with strong magnets

## Raspberry Pi Fritzing diagram
![Fritzing](https://raw.githubusercontent.com/philm400/Raspberry-Pi-Python-Scalextric-Lap-Timer/master/docs/img/Scalextric-Reed-Swtichs_diagram.png?raw=true)
