"""PCF8574/A library

Micropython 1.10

This library aims to add compatibility with machine.Pin behaviour over PCF8574 class.

Damien "psolyca" Gaignon <damien.gaignon@gmail.com>
"""


class PCFPin():
    """Class to mimic machine.Pin or machine.Signal classes + more

    This class aims to add compatibility for PCF8574 class with other
    classes which use Pin class like the asynchronous switch class "aswitch".

    Parameters:
        pcf :   PCF8574 device
        pin :   pin to monitor
    """

    def __init__(self, pcf, pin):
        self._pcf = pcf
        self._pin = bytes([pin])
        # Initial state, useful for output toggle
        self._state = bytearray([pcf.read_pin(pin)])
        self._inverted = bytearray([pcf.inverted[0] >> pin & 1])

    def value(self, value=None):
        """Get or set the value of the pin

        If an argument argument is supplied, the pin is set to the value

        Parameters:
            value (bool, optional)

        Returns:
            (int)
        """
        if value is None:
            return self._pcf.read_pin(self._pin[0])
        else:
            self._pcf.write_pin(self._pin[0], value)
            self._state[0] = value

    def on(self):
        """Activate the pin"""
        self.value(self._inverted[0])

    def off(self):
        """Desactivate the pin"""
        self.value(not self._inverted[0])

    def toggle(self):
        """Toggle the pin in output mode"""
        self._state[0] = not self._state[0]
        self._pcf.write_pin(self._pin[0], self._state[0])

    def mode(self, value=None, invert=False):
        """Get or set the pin mode (input or output)

        Parameters:
            value (str, optional) : "IN" or "OUT"
            invert (bool, optional) :   True inverted pin,
                False non inverted pin. Default to False.

        Returns:
            (int) : 1 for input, 0 for output
        """
        if value is None:
            return self._pcf.directions[self._pin[0]]
        else:
            if value == "IN":
                self._pcf.input_pin(self._pin[0], invert)
            else:
                self._pcf.output_pin(self._pin[0], invert)
            self._inverted[0] = invert

    def input(self):
        """Set the pin as input"""
        self.mode("IN", self._inverted[0])

    def output(self):
        """Set the pin as output"""
        self.mode("OUT", self._inverted[0])

    def inverted(self):
        """Set the pin as inverted"""
        if self._inverted[0] == 0:
            self._pcf.invert_pin(self._pin[0], True)
            self._inverted[0] = 1
            self._state[0] = not self._state[0]

    def noninverted(self):
        """Set the pin as non inverted"""
        if self._inverted[0] == 1:
            self._pcf.invert_pin(self._pin[0], False)
            self._inverted[0] = 0
            self._state[0] = not self._state[0]