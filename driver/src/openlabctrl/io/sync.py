from enum import Enum
class SyncCmd(Enum):
    TrigSrc = 0x0


class TriggerSource(Enum):
    """
    IO Sync Frame execution trigger source.
    """
    NONE = 0x0
    EXT_HIGH = 0x1
    EXT_LOW = 0x2
    EXT_RISE = 0x3
    EXT_FALL = 0x4
    EXT_RISE_FALL = 0x5
    _SYNC_DAISY_CHAIN = 0x6




from .base import BaseIo

class Sync (BaseIo):
    _requires_done_instruction = False

    def __init__(self, addr, clk_freq):
        super().__init__(addr, clk_freq)

    def trigger(self, src: TriggerSource):
        if src not in TriggerSource:
            raise Exception(f"Trigger source {src} is not valid. Should be of type TriggerSource or None.")
        self._add_instruction(cmd=SyncCmd.TrigSrc.value, data=src.value)
        self._locked = True

