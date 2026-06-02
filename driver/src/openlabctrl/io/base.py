from enum import Enum
import numpy as np


class BaseIoCmd(Enum):
    NOP = 0xF
    DONE = 0xE



PREALLOCATION_BLOCK_LEN = 0x1000

class BaseIo():
    _requires_done_instruction = True #Whether the IO requires a DONE instruction at the end of the instruction list
    _t_overflow = (1 << 24) - 32 #Number of clk cycles after which time value overflows (set to 2^24 - margin for latency compensations)

    def __init__(self, addr, clk_freq):
        self._addr = addr
        self._clk_freq = clk_freq
        self._tlast = 0
        self._tnext = 0
        self._tincr = 1
        self._t_list = np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)
        self._instr_list = np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)
        self._idx = 0
        self._preallocation_len = PREALLOCATION_BLOCK_LEN
        self._locked = False
    
    
    def reset(self):
        """
        Reset IO instruction cache and time base.
        """
        self._tlast = 0
        self._tnext = 0
        self._tincr = 1
        self._t_list = np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)
        self._instr_list = np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)
        self._idx = 0
        self._preallocation_len = PREALLOCATION_BLOCK_LEN
        self._locked = False

    def _add_instruction(self, cmd: int, data: int, duration: int = 1):        
        #Check if instruction list is locked
        if self._locked:
            raise Exception("Cannot add instruction because the instruction list is locked. Please reset instruction list.")
        
        #Map to uint64
        cmd = np.uint64(cmd)
        data = np.uint64(data)
        duration = np.uint64(duration)

        #Assign time for instruction
        t = self._tnext
        
        #Insert NOP instructions every t_overflow clk cycles (if needed)
        while (t - self._tlast) > self._t_overflow:
            self._tnext = self._tlast + self._t_overflow
            self._add_instruction(cmd=BaseIoCmd.NOP.value, data=0, duration=self._t_overflow)

        #Preallocate more space if needed
        if self._idx >= self._preallocation_len:
            self._instr_list = np.concatenate((self._instr_list, np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)))
            self._t_list = np.concatenate((self._t_list,  np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)))
            self._mask_list = np.concatenate((self._mask_list,  np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint32)))
            self._preallocation_len += PREALLOCATION_BLOCK_LEN

        #Create new instruction
        #63 - 60 | 59 - 56 | 55 - 32 | 31 - 0
        #Addr    |   Cmd   |   Time  |   Data
        instr = ((self._addr << 60) | (cmd << 56) | ((t & 0xffffff) << 32) | data)
        
        #Add instruction to list
        self._instr_list[self._idx] = instr
        self._t_list[self._idx] = t
        self._idx += 1
        self._tlast = t
        self._tnext = t + max(duration, self._tincr)

        return 

    def _add_done_instruction(self):
        self._add_instruction(cmd=BaseIoCmd.DONE.value, data=0)
        self._locked = True

    def _get_instruction_and_time_list(self):
        if not self._locked:
            if self._requires_done_instruction:
                self._add_done_instruction()
                instr_list = self._instr_list[:self._idx]
                
        instr_list = self._instr_list[:self._idx]
        t_list = self._t_list[:self._idx]
        return instr_list, t_list  


    def get_time(self) -> int:
        """
        Retrieve current IO time (in units of CLK cycles).
        """
        return self._tnext

    def set_time(self, val: int):
        """
        Set new IO time (should be larger or equal than current IO time).

        :param val: time (in units of clk cycles).

        """
        if val < self._tnext:
            raise Exception(f"Cannot set time to {val} because it is smaller than current time {self._tnext}.")
        self._tnext = np.uint64(val)
    def set_time_increment(self, val: int):
        """
        Set IO instruction time increment, i.e. time between consecutive IO instructions. Default time increment after reset is 1 clk cycle.

        :param val: time increment (in units of clk cycles).
        """
        if val <= 0:
            raise Exception(f"Time increment must be a positive integer. Got {val} instead.")
        self._tincr = np.uint64(val)

    def get_time_increment(self) -> int:
        """
        Retrieve current IO time increment (in units of clk cycles).
        """
        return self._tincr
    
    def delay(self, val: int):
        """
        Increment current IO time by a specified delay time. Used to retard following IO instruction.

        :param val: Delay time (in units of clk cycles).

        """
        t = self.get_time()
        self.set_time(t + val)

    def _is_locked(self):
        return self._locked
    

    



