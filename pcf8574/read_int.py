#
# PCF8574 library
#
# Author : Damien "psolyca" Gaignon <damien.gaignon@gmail.com>
#
# Example for PCF8574 library with interrupt
#

import machine

import pcf8574
import pcf8574pin

# I2C pins are GPIO4 (SCL) and GPIO5 (SDA)
# PCF8574 use 100 kHz mode
i2c=machine.I2C(scl=machine.Pin(4),
                sda=machine.Pin(5),
                freq=100000)

# PCF8574 is at address 0x38
# Pins 0 to 3 are input non inverted
# Pins 4 to 7 are output inverted (relay board for example)
pcf=pcf8574.PCF8574(i2c,
                    0x38,
                    direction='11110000',
                    state='11110000',
                    inverted='00001111')

# Interrupt pin is GPIO12
pcf.enable_int(12)

# Quit by connecting GPIO12 to ground
pin = machine.Pin(12,
                  machine.Pin.IN,
                  machine.Pin.PULL_UP)

while True:

    # Interrupt routine
    if pcf.interrupt > 0:

        for pin in range(8):
            if pcf.changed_pins[pin * 2]:
                print("New value of pin {:d} is : {:d}".format(pin,
                      pcf.changed_pins[pin * 2 + 1]))
        pcf.reset_int()

    if not pin.value():
        break
