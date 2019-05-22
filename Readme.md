# micropython-librairies
Micropython library for PCF8574/A.

## Usage
To use this script in your firmware, it should be placed into micropython filesystem using (ampy)[https://github.com/pycampers/ampy] or (rshell)[https://github.com/dhylands/rshell] and imported, e.g:

`from pcf8574 import PCF8574`.

To minimize memory usage, (the official documentation)[http://docs.micropython.org/en/latest/reference/constrained.html] has been followed.
In order to minimize file size on the system, scripts on the main branch of this repository do not contain docstrings. Thus, a special branch has been made with documented scripts.

## Precompilation
To save space and time, scripts could be pre-compiled as follow.
### Bytecode
This method will generate micropython bytecode `.mpy` files that can be imported just like normal scripts after installed in the filesystem.
In order to get bytecode, you need to compile the cross-compiler `mpy-cross` (compiled by default with the firmware), it can be used like this:

`MICROPYTHON_ROOT_DIR/mpy-cross/mpy-cross pcf8574.py`


### Freezing module
However, these files still reside in filesystem.
To optimize further, they can be "freezed" into the firmware (Flash memory). This will make them permanent. This can be done by placing them inside target's `modules` or `scripts` folder, e.g:

`MICROPYTHON_ROOT_DIR/esp8266/modules/`

`MICROPYTHON_ROOT_DIR/esp8266/scripts/`

The difference between the two is that scripts in `modules` folder gets compiled into bytecode with `mpy-cross` tool like above, while those in `scripts` will be just freezed into Flash. Note that only `.py` scripts should be placed in both folders as anything else can cause firmware corruption. After placing scripts in either of them, rebuild is needed. This will generate new firmware image that can be flashed like usual. The scripts are immediately available using the `import` syntax from above.
Neither of these files will be visible when listing the filesystem with os.listdir().

## Examples
You can find examples in the module directory.
* `read_int.py` for interrupt usage
* `read_aswitch.py` for aswitch and uasyncio usage

