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
    """Class to control a PCF8574/A IC

    Parameters:
        i2c (:obj:`I2C`) : I2C peripheral
        address (int) : Address of the PCF8574/A device
        direction (str, optional) : Direction of pins

            String representation of each pin (1 input / 0 output)

            '10100110' = input, output, input, output\*2, input\*2, output
        state (str, optional) : Initial digital state of pins (physical),

            String representation of each pin (1 on / 0 off for output,
            1 for input)

            '10101111' = input, off, input, off, on, input\*2, on
        inverted (str, optional) : Inverted pins

            String representation of each pin (1 inverted / 0 non inverted)

            '11100011' = inverted\*3, non\*3, inverted\*2

    Attributes:
        interrupt (int): counter for interruption
        changed_pins (bytearray):  bytearray of [pin/value] * 8 where `pin` 
            is set to 1 when changed and `value` is the new value of the pin.
    """

    INPUT = 1
    OUTPUT = 0
    UNDEF = 2

    def __init__(self, i2c, address, direction=None, state=None, inverted=None):
        self._i2c = i2c
        self._address = address
        # Direction of pins
        self._directions = bytearray([self.UNDEF] * 8)
        # Input pins bitmask
        self._input = bytearray(1)
        # Inverted pins bitmask
        self._inverted = bytearray(1)
        # Logical state of pins (inverted)
        self._lstate = bytearray(1)
        # Digital state of pins (non inverted)
        self._dstate = bytearray(1)
        # Flag to avoid one/multiple use of read and/or write from/to IC
        self._dstatef = False
        # Pre-allocate interrupt handler
        self._alloc_poll = self._poll
        # Interruption counter
        self.interrupt = 0
        # Array of changed pins for interruption ([pin\value] * 8)
        self.changed_pins = bytearray(16)

        if direction is not None:
            direction = list(direction)
            self._directions = bytearray(int(x) for x in direction)
            self._input[0] = int(''.join(reversed(direction)),2)
        if inverted is not None:
            self._inverted[0] = int(''.join(reversed(list(inverted))),2)
        if state is not None:
            self._lstate[0] = int(''.join(reversed(list(state))),2)
            self._dstate[0] = self._lstate[0] ^ self._inverted[0]
            self._dstate[0] = self._dstate[0] | self._input[0]
            self._i2c.writeto(self._address, self._dstate)

    def __repr__(self):
        """Bit representation of pin states"""
        return "{:08b}".format(self._lstate[0])

    def _alter_bitmask(self, bitmask, pin, value=True):
        """Set/clear one bit in a bitmask.

        Parameters:
            bitmask (bytearray) :   bitmask to alter
            pin (int):              pin 0-7 to change
            value (bool, optional): True to set (default) / False to clear

        Returns:
            bytearray: Altered bitmask
        """
        if value:
            return bytearray([bitmask[0] | (1 << pin)])
        else:
            return bytearray([bitmask[0] & ~(1 << pin)])

    def _write_state(self):
        """Write the state to IC

        The method takes care of inverted pins and input pins
        """
        if not self._dstatef:
            self._dstatef = True
            # Inverted pins
            self._dstate[0] = self._lstate[0] ^ self._inverted[0]
            # Input pins to high
            self._dstate[0] = self._dstate[0] | self._input[0]
            self._i2c.writeto(self._address, self._dstate)
            self._dstatef = False

    def _read_state(self):
        """Read the state of IC

        The method takes care of inverted pins
        """
        if not self._dstatef:
            self._dstatef = True
            self._dstate = bytearray(self._i2c.readfrom(self._address, 1))
            # Inverted pins
            self._lstate[0] = self._dstate[0] ^ self._inverted[0]
            self._dstatef = False

    def read_pin(self, pin):
        """Read value of a pin

        Parameters:
            pin (int):  pin 0-7

        Returns:
            int: The pin value 0 or 1
        """
        # Update self._lstate
        self._read_state()
        return self._lstate[0] >> pin & 1

    def write_pin(self, pin, value):
        """Write value to an output pin

        Parameters:
            pin (int):      pin 0-7
            value (bool) :  value to write
        """
        if self._directions[pin] == self.OUTPUT:
            self._lstate = self._alter_bitmask(self._lstate, pin, value)
            self._write_state()

    def input_pin(self, pin, invert=False):
        """Set pin(s) as input

        Parameters:
            pin (int or list): pin 0-7
            invert (bool, optional) : True inverted pin, False non
                inverted pin. Defaults to False.
            
                If a list of pins is given, invert applies to all pins
        """
        if type(pin) == list:
            for p in pin:
                self._inverted = self._alter_bitmask(self._inverted, pin, invert)
                self._input = self._alter_bitmask(self._input, pin, True)
                self._directions[pin] = self._input
        else:
            self._inverted = self._alter_bitmask(self._inverted, pin, invert)
            self._input = self._alter_bitmask(self._input, pin, True)
            self._directions[pin] = self._input
        self._lstate[0] = self._dstate[0] ^ self._inverted[0]

        self._write_state()

    def output_pin(self, pin, invert=False):
        """Set pin(s) as output

        Parameters:
            pin (int or list): pin 0-7
            invert (bool, optional) : True inverted pin, False non
                inverted pin. Defaults to False.
            
                If a list of pins is given, invert applies to all pins
        """
        if type(pin) == list:
            for p in pin:
                self._inverted = self._alter_bitmask(self._inverted, pin, invert)
                self._input = self._alter_bitmask(self._input, pin, False)
                self._directions[pin] = self.OUTPUT
        else:
            self._inverted = self._alter_bitmask(self._inverted, pin, invert)
            self._input = self._alter_bitmask(self._input, pin, False)
            self._directions[pin] = self.OUTPUT
        self._lstate[0] = self._dstate[0] ^ self._inverted[0]

        self._write_state()

    def invert_pin(self, pin, invert=False):
        """Set a pin has inverted or not

        Previous state is kept

        Parameters:
            pin (int or list) :  pin 0-7
            invert (bool, optional) : True inverted pin, False non
                inverted pin. Defaults to False.
            
                If a list of pins is given, invert applies to all pins
        """
        if type(pin) == list:
            for p in pin:
                self._inverted = self._alter_bitmask(self._inverted, pin, invert)
        else:
            self._inverted = self._alter_bitmask(self._inverted, pin, invert)
        self._lstate[0] = self._dstate[0] ^ self._inverted[0]

        self._write_state()

    def _poll(self, _):
        """Poll for changes on the PCF8574/A after interruption

        To get the changed pins, use the `changed_pins` attribut.
        """
        self._dstate[0] = self._i2c.readfrom(self._address, 1)[0]

        readstate = bytearray([self._dstate[0] ^ self._inverted[0]])
        for pin in range(8):
            if self._directions[pin] == self._input:
                # Check if the pin has changed
                if (self._lstate[0] >> pin & 1) != (readstate[0] >> pin & 1):
                    # Changed the state of the pin
                    self._lstate = self._alter_bitmask(
                        self._lstate,
                        pin,
                        readstate[0] >> pin & 1)
                    self.changed_pins[pin * 2] = 1
                    self.changed_pins[pin * 2 + 1] = readstate[0] >> pin & 1
        self.interrupt +=1

    def enable_int(self, pin):
        """Enable input interrupt

        To get the changed pins, use the attribut `changed_pins`

        Parameters:
            pin (int): interrupt pin
        """
        # Initialize changed_pins default value
        for p in range(8):
            self.changed_pins[p * 2 + 1] = self._lstate[0] >> p & 1
        self._int_pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self._int_pin.irq(trigger = machine.Pin.IRQ_FALLING,
                        handler = self._alloc_poll
                        )

    def reset_int(self):
        """Reset interrupt

        Use this method after using the interrupt
        """
        state = machine.disable_irq()
        for pin in range(8):
            self.changed_pins[pin * 2 ] = 0
        self.interrupt -= 1
        machine.enable_irq(state)
    
    def disable_int(self):
        """Disable interrupt"""
        machine.disable_irq()
        self.changed_pins = bytearray(16)
        self.interrupt = 0

    def inverted(self, pin):
        """Return the inverted state of a pin

        Parameters:
            pin (int): pin 0-7

        Returns:
            int: 1 for inverted, 0 for non inverted
        """
        return self._inverted[0] >> pin & 1

    def direction(self, pin):
        """Return the direction of a pin

        Parameters:
            pin (int): pin 0-7

        Returns:
            int: 1 for input, 0 for output
        """
        return self._directions[pin]