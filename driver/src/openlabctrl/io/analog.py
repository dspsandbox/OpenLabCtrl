from enum import Enum
from .base import BaseIo

class AnalogOutCmd(Enum):
    DUTY_CYCLE = 0x0

class AnalogOut(BaseIo): 
    """
    Driver class for low speed analog IOs (PWM + Low Pass Filter).
    """
    def __init__(self, addr, clk_freq):
        super().__init__(addr, clk_freq)

    def duty_cycle(self, val: float):
        """
        Define scale of underlying Sigma-Delta Modulator.

        :param val: Relative scale in range [0.0, 1.0].
        """
        DUTY_CYCLE_MIN = 0.0
        DUTY_CYCLE_MAX = 1.0
        MODULATION_DEPTH = 12
        if (val < DUTY_CYCLE_MIN) or (val > DUTY_CYCLE_MAX):
            raise Exception(f"Duty cycle value {val} is out of range [{DUTY_CYCLE_MIN}, {DUTY_CYCLE_MAX}].")
        data = int(val * ((1 << MODULATION_DEPTH) - 1))
        self._add_instruction(cmd=AnalogOutCmd.DUTY_CYCLE.value, data=data)