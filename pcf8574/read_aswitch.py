#
# PCF8574 library
#
# Author : Damien "psolyca" Gaignon <damien.gaignon@gmail.com>
#
# Example for PCF8574 library with aswitch
# to show the use of a PCF8574/A as input and output
#

import machine

import uasyncio as asyncio

from pcf8574 import PCF8574
from pcf8574pin import PCFPin

from aswitch import Switch



# I2C pins are GPIO4 (SCL) and GPIO5 (SDA)
# PCF8574 use 100 kHz mode
i2c=machine.I2C(scl=machine.Pin(4),
                sda=machine.Pin(5),
                freq=100000)

# PCF8574 is at address 0x38
# Pins 0 to 3 are input non inverted
# Pins 4 to 7 are output inverted (relay board for example)
pcf=PCF8574(i2c,
            0x38,
            direction='11110000',
            state='11110000',
            inverted='00001111')

# Callback for aswitch
def toggle(relay):
    relay.toggle()

# Quit by connecting GPIO12 to ground
async def killer():
    pin = machine.Pin(12,
                      machine.Pin.IN,
                      machine.Pin.PULL_UP)
    while pin.value():
        await asyncio.sleep_ms(50)

# Switch with a callback (a coro could be used)
def sw_start():

    pin = PCFPin(pcf, 0)
    relay = PCFPin(pcf, 4)

    sw = Switch(pin)
    sw.close_func(toggle, (relay,))
    sw.open_func(toggle, (relay,))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(killer())

