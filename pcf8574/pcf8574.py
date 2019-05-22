"""PCF8574/A library

Micropython 1.10

This library aims to control PCF8574/A device through I2C.

Damien "psolyca" Gaignon <damien.gaignon@gmail.com>
"""

import utime

import machine
import micropython

micropython.alloc_emergency_exception_buf(100)

class DirectionException(Exception):
    pass


class PCF8574():

    INPUT = 1
    OUTPUT = 0
    UNDEF = 2

    def __init__(self, i2c, address, direction=None, state=None, inverted=None):
        self._i2c = i2c
        self._address = address
        # Direction of pins
        self.directions = bytearray([self.UNDEF] * 8)
        # Input pins bitmask
        self.input = bytearray(1)
        # Inverted pins bitmask
        self.inverted = bytearray(1)
        # Logical state of pins (inverted)
        self.lstate = bytearray(1)
        # Digital state of pins (non inverted)
        self.dstate = bytearray(1)
        # Flag to avoid one/multiple use of read and/or write from/to IC
        self.dstatef = False
        # Pre-allocate interrupt handler
        self._alloc_poll = self._poll
        # Interruption counter
        self.interrupt = 0
        # Array of changed pins for interruption ([pin\value] * 8)
        self.changed_pins = bytearray(16)

        if direction is not None:
            direction = list(direction)
            self.directions = bytearray(int(x) for x in direction)
            self.input[0] = int(''.join(reversed(direction)),2)
        if inverted is not None:
            self.inverted[0] = int(''.join(reversed(list(inverted))),2)
        if state is not None:
            self.lstate[0] = int(''.join(reversed(list(state))),2)
            self.dstate[0] = self.lstate[0] ^ self.inverted[0]
            self.dstate[0] = self.dstate[0] | self.input[0]
            self._i2c.writeto(self._address, self.dstate)

    def __repr__(self):
        """Bit representation of pin states"""
        return "{:08b}".format(self.lstate[0])

    def _alter_bitmask(self, bitmask, pin, value=True):
        if value:
            return bytearray([bitmask[0] | (1 << pin)])
        else:
            return bytearray([bitmask[0] & ~(1 << pin)])

    def _write_state(self):
        if not self.dstatef:
            self.dstatef = True
            # Inverted pins
            self.dstate[0] = self.lstate[0] ^ self.inverted[0]
            # Input pins to high
            self.dstate[0] = self.dstate[0] | self.input[0]
            self._i2c.writeto(self._address, self.dstate)
            self.dstatef = False

    def _read_state(self):
        if not self.dstatef:
            self.dstatef = True
            self.dstate = bytearray(self._i2c.readfrom(self._address, 1))
            # Inverted pins
            self.lstate[0] = self.dstate[0] ^ self.inverted[0]
            self.dstatef = False

    def read_pin(self, pin):
        # Update self.lstate
        self._read_state()
        return self.lstate[0] >> pin & 1

    def write_pin(self, pin, value):
        if self.directions[pin] == self.OUTPUT:
            self.lstate = self._alter_bitmask(self.lstate, pin, value)
            self._write_state()

    def input_pin(self, pin, invert=False):
        if type(pin) == list:
            for p in pin:
                self.inverted = self._alter_bitmask(self.inverted, pin, invert)
                self.input = self._alter_bitmask(self.input, pin, True)
                self.directions[pin] = self.INPUT
        else:
            self.inverted = self._alter_bitmask(self.inverted, pin, invert)
            self.input = self._alter_bitmask(self.input, pin, True)
            self.directions[pin] = self.INPUT
        self.lstate[0] = self.dstate[0] ^ self.inverted[0]

        self._write_state()

    def output_pin(self, pin, invert=False):
        if type(pin) == list:
            for p in pin:
                self.inverted = self._alter_bitmask(self.inverted, pin, invert)
                self.input = self._alter_bitmask(self.input, pin, False)
                self.directions[pin] = self.OUTPUT
        else:
            self.inverted = self._alter_bitmask(self.inverted, pin, invert)
            self.input = self._alter_bitmask(self.input, pin, False)
            self.directions[pin] = self.OUTPUT
        self.lstate[0] = self.dstate[0] ^ self.inverted[0]

        self._write_state()

    def invert_pin(self, pin, invert=False):
        if type(pin) == list:
            for p in pin:
                self.inverted = self._alter_bitmask(self.inverted, pin, invert)
        else:
            self.inverted = self._alter_bitmask(self.inverted, pin, invert)
        self.lstate[0] = self.dstate[0] ^ self.inverted[0]

        self._write_state()

    def _poll(self, _):
        self.dstate[0] = self._i2c.readfrom(self._address, 1)[0]

        readstate = bytearray([self.dstate[0] ^ self.inverted[0]])
        for pin in range(8):
            if self.directions[pin] == self.INPUT:
                # Check if the pin has changed
                if (self.lstate[0] >> pin & 1) != (readstate[0] >> pin & 1):
                    # Changed the state of the pin
                    self.lstate = self._alter_bitmask(
                        self.lstate,
                        pin,
                        readstate[0] >> pin & 1)
                    self.changed_pins[pin * 2] = 1
                    self.changed_pins[pin * 2 + 1] = readstate[0] >> pin & 1
        self.interrupt +=1

    def enable_int(self, pin):
        # Initialize changed_pins default value
        for p in range(8):
            self.changed_pins[p * 2 + 1] = self.lstate[0] >> p & 1
        self._int_pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self._int_pin.irq(trigger = machine.Pin.IRQ_FALLING,
                        handler = self._alloc_poll
                        )

    def reset_int(self):
        state = machine.disable_irq()
        for pin in range(8):
            self.changed_pins[pin * 2 ] = 0
        self.interrupt -= 1
        machine.enable_irq(state)
    
    def disable_int(self):
        machine.disable_irq()
        self.changed_pins = bytearray(16)
        self.interrupt = 0