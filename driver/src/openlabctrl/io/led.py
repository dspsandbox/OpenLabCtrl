from enum import Enum
from .base import BaseIo

class LedCmd(Enum):
    OUTPUT = 0x0

class Led(BaseIo):
    """
    Driver class for the onboard LEDs.
    """
    def __init__(self, addr, clk_freq):
        super().__init__(addr, clk_freq)

    def output(self, val: int, mask: int = 0xffff):
        """
        Set the on/off state of masked LEDs.
        E.g. ``val=0b0010`` and ``mask=0b1010`` will result in LED[0] -> unchanged, LED[1] -> on, LED[2] -> unchanged and LED[3] -> off.

        :param val: LED state value (1 = on, 0 = off).
        :param mask: Bit mask for selecting which LEDs to update.
        """
        self._add_instruction(cmd=LedCmd.OUTPUT.value, data=((mask << 16) | val))
        

    