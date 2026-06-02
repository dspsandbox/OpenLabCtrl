from enum import Enum
from .base import BaseIo

class DigitalIoCmd(Enum):
    OUTPUT = 0x0
    TRISTATE = 0x1

class DigitalIo(BaseIo):
    """
    Driver class for Digital IOs.

    .. note::
        Ports configured as inputs (high-impedance via :meth:`tristate`) include internal pull-up resistors and will idle high when left undriven.
    """
    def __init__(self, addr, clk_freq):
        super().__init__(addr, clk_freq)

    def output(self, val: int, mask: int = 0b1111):
        """
        Set output value of masked ports (requires ports to be defined as outputs via :meth:`DigitalIo.tristate`).
        E.g. ``val=0b0010`` and ``mask=0b1010`` will result in port[0] -> unchanged, port[1] -> 1, port[2] -> unchanged and port[3] -> 0.

        :param val: Output value.
        :param mask: Bit mask for updating digital ports.
        """
        self._add_instruction(cmd=DigitalIoCmd.OUTPUT.value, data=((mask << 16) | val))

    def tristate(self, val: int, mask: int = 0b1111):
        """
        Set direction (output/tristate) of masked ports.
        A ``0`` bit configures the corresponding port as a driven output; a ``1`` bit puts it in high-impedance (input) mode.
        E.g. ``val=0b0010`` and ``mask=0b1010`` will result in port[0] -> unchanged, port[1] -> high-Z (input), port[2] -> unchanged and port[3] -> driven (output).

        :param val: Direction value (0 = driven output, 1 = high-impedance / input).
        :param mask: Bit mask for updating digital ports.
        """
        self._add_instruction(cmd=DigitalIoCmd.TRISTATE.value, data=((mask << 16) | val))

    