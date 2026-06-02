from .base import BaseIo
from enum import Enum

CLK_FREQ = 125e6

class RfCmd(Enum):
    PHASE = 0x0
    PHASE_RST = 0x1
    FREQ = 0x2
    AMPL = 0x3
    UPDATE = 0x8
    

class RfBase(BaseIo):
    """
    Base driver class for RF IOs (DDS-based signal generation).

    Wraps a direct digital synthesizer (DDS) core and provides control over
    frequency, phase, and amplitude. The ``update`` flag on each method controls
    whether the new value is applied immediately (``True``) or staged for a later
    atomic update (``False``), which allows frequency, phase, and amplitude to be
    changed simultaneously.
    """
    def __init__(self, addr, clk_freq):
        super().__init__(addr, clk_freq)

    def frequency(self, val: float, update: bool = True):
        """
        Set the output frequency.

        The valid range is ``[-clk_freq/2, clk_freq/2]`` (i.e. ±62.5 MHz for a 125 MHz clock).

        :param val: Frequency in Hz.
        :param update: If ``True``, apply the new value immediately. Set to ``False`` to stage
            the change and apply it atomically together with other staged parameters.
        """
        FREQ_MIN = -self._clk_freq / 2
        FREQ_MAX = self._clk_freq / 2
        if (val < FREQ_MIN) or (val > FREQ_MAX):
            raise Exception(f"Frequency value {val} is out of range [{FREQ_MIN}, {FREQ_MAX}].")
        cmd = RfCmd.FREQ.value
        if update:
            cmd |= RfCmd.UPDATE.value
        data = int(val / self._clk_freq * ((1 << 32) - 1))
        self._add_instruction(cmd=cmd, data=data)

    def phase(self, val: float, update: bool = True):
        """
        Set the output phase.

        :param val: Phase in degrees.
        :param update: If ``True``, apply the new value immediately. Set to ``False`` to stage
            the change and apply it later with other staged parameters.
        """
        cmd = RfCmd.PHASE.value
        if update:
            cmd |= RfCmd.UPDATE.value
        data = int((val % 360) / 360 * ((1 << 32) - 1))
        self._add_instruction(cmd=cmd, data=data)

    def amplitude(self, val: float, update: bool = True):
        """
        Set the output amplitude.

        :param val: Relative amplitude in range ``[-1, 1]``.
        :param update: If ``True``, apply the new value immediately. Set to ``False`` to stage
            the change and apply it later with other staged parameters.
        """
        AMPL_MIN = -1
        AMPL_MAX = 1
        if (val < AMPL_MIN) or (val > AMPL_MAX):
            raise Exception(f"Amplitude value {val} is out of range [{AMPL_MIN}, {AMPL_MAX}].")
        cmd = RfCmd.AMPL.value
        if update:
            cmd |= RfCmd.UPDATE.value
        data = int(val * ((1 << 15) - 1))
        self._add_instruction(cmd=cmd, data=data)

    def phase_reset(self, update: bool = True):
        """
        Reset the DDS phase accumulator to zero.

        :param update: If ``True``, apply immediately. Set to ``False`` to stage the reset
            and apply it later with other staged parameters.
        """
        cmd = RfCmd.PHASE_RST.value
        if update:
            cmd |= RfCmd.UPDATE.value
        self._add_instruction(cmd=cmd, data=1)


class RfOut(RfBase):
    """
    Driver class for RF output channels.
    """
    def __init__(self, addr, clk_freq):
        super().__init__(addr, clk_freq)


class RfIn(RfBase):
    """
    Driver class for RF input channels (TODO: missing FPGA backend).
    """
    def __init__(self, addr, clk_freq):
        super().__init__(addr, clk_freq)

    

