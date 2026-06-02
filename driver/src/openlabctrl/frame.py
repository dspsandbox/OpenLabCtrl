from __future__ import annotations
import numpy as np
import copy
from .io.sync import TriggerSource


PREALLOCATION_BLOCK_LEN = 0x10000

class IoSyncFrame:
    """IO instruction container with independent time-base.

    At instantiation, an IO instance is created for each entry in
    ``device_type.IO_DICT`` and exposed as an attribute with the same name.
    The exact set of attributes therefore depends on the device type passed
    (e.g. see RP 125-14 Base :attr:`~openlabctrl.device.rp_125_14.Rp_125_14.IO_DICT`).

    :param device_type: Device class (not instance)
    :param trig: Trigger source to initiate frame execution. If ``None`` or ``TriggerSource.NONE``, frame is triggered immediately.
    """

    def __init__(self, device_type, trig: TriggerSource | None = None):
        if trig is None:
            trig = TriggerSource.NONE
        if trig not in TriggerSource:
            raise Exception(f"Trigger source {trig} is not valid. Should be of type TriggerSource or None.")
        self._device_type = device_type
        self._trig = trig
        self._io_dict = {}
        self._idx = 0
        for io_name in self._device_type.IO_DICT.keys():
            io_class = self._device_type.IO_DICT[io_name]["class"]
            io_addr = self._device_type.IO_DICT[io_name]["addr"]
            clk_freq = self._device_type.CLK_FREQ
            self._io_dict[io_name] = io_class(addr=io_addr, clk_freq=clk_freq)
        self._set_sync()
        self._instr_list = np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)
        self._preallocation_len = PREALLOCATION_BLOCK_LEN



    def __getattr__(self, name):
        io_dict = object.__getattribute__(self, "_io_dict")
        if name in io_dict:
            return io_dict[name]
        raise AttributeError(name)

    def reset(self):
        """
        Reset all IOs (instruction lists and time-base).
        """
        for io in self._io_dict.values():
            io.reset()
        self._set_sync()
        self._instr_list = np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)
        self._preallocation_len = PREALLOCATION_BLOCK_LEN
        self._idx = 0

    def _set_sync(self):
        self._io_dict["_sync"].trigger(src=self._trig)

    def _is_locked(self):
        return all(io._is_locked() for io in self._io_dict.values())

    def _get_instruction_list(self):
        if self._is_locked():
            return self._instr_list[:self._idx]
        else:
            #Retrieve instruction lists and last instruction index for each IO
            idx_max_dict = {}
            instr_list_dict = {}
            t_list_dict = {}
            for io_name in self._io_dict.keys():
                instr_list, t_list = self._io_dict[io_name]._get_instruction_and_time_list()
                idx_max_dict[io_name] = len(instr_list)
                instr_list_dict[io_name] = instr_list
                t_list_dict[io_name] = t_list

            #Create dictionaries for iteration variables
            idx_dict = {}
            t_dict = {}
            for io_name in self._io_dict.keys():
                idx_dict[io_name] = 0
                t_dict[io_name] = 0


            #Iterate over instructions for all IOs in chronological order
            t = 0
            idx = 0
            keep_iterating = True
            while keep_iterating:
                keep_iterating = False

                if idx >= self._preallocation_len:
                    self._instr_list = np.concatenate((self._instr_list, np.zeros(PREALLOCATION_BLOCK_LEN, dtype=np.uint64)))
                    self._preallocation_len += PREALLOCATION_BLOCK_LEN

                for io_name in self._io_dict.keys():
                    io_idx = idx_dict[io_name]
                    io_idx_max = idx_max_dict[io_name]
                    if io_idx < io_idx_max:
                        keep_iterating = True
                        io_t = t_list_dict[io_name][io_idx]
                        io_t_previous = t_list_dict[io_name][io_idx - 1]
                        if (io_idx == 0) or (io_t_previous <= t):
                            self._instr_list[idx] = instr_list_dict[io_name][io_idx]
                            t_dict[io_name] = io_t
                            t = max(t, io_t)
                            idx_dict[io_name] += 1
                            idx += 1
            self._idx = idx
            return self._instr_list[:self._idx]




    def set_time(self, t : int):
        """
        Set new time for all IOs of this frame, see :meth:`~openlabctrl.io.base.BaseIo.set_time`.

        :param t: time (in units of clk cycles). 
        """
        for io in self._io_dict.values():
            io.set_time(t)

    def set_time_increment(self, t_incr : int):
        """
        Set new time increment for all IOs of this frame, see :meth:`~openlabctrl.io.base.BaseIo.set_time_increment`.
        """ 
        for io in self._io_dict.values():
            io.set_time_increment(t_incr)

    def rsync(self):
        """
        Time-aligns all IOs of this frame. The backend retrieves the current time of all IOs and sets them to the latest (largest) value.
        """
        tmax = max(io.get_time() for io in self._io_dict.values())
        self.set_time(tmax)

    def delay(self, val : int):
        """
        Delay all IOs of this frame, see :meth:`~openlabctrl.io.base.BaseIo.delay`.

        :param val: Delay time (in units of clk cycles).
        """
        for io in self._io_dict.values():
            io.delay(val)


    def _get_acquisition_dict(self):
        acq_dict = {}
        for io_name in self._io_dict.keys():
            if "scope" in io_name:
                acq_dict[io_name] = self._io_dict[io_name]._get_acquisition_dict()
        return acq_dict




class ParametrizedIoSyncFrame():
    """
    Parametrized version of :class:`IoSyncFrame`, which builds upon a frame function and a frame parameter set.
    To reduce overall compilation time, parametrized IO sync frames are (re-)compiled only when changes in the frame function
    or the frame parameter set are detected.
    """
    def __init__(self, device_type, trig: int | None = None):
        if trig is None:
            trig = TriggerSource.NONE
        if trig not in TriggerSource.__dict__.values():
            raise Exception(f"Trigger source {trig} is not valid. Valid sources are: {list(TriggerSource.__dict__.values())}.")
        self._device_type = device_type
        self._trig = trig
        self._frame = IoSyncFrame(device_type=device_type, trig=trig)
        self._frame_args = ()
        self._frame_kwargs = {}
        self._frame_args_last = ()
        self._frame_kwargs_last = {}
        self._frame_func = None

    def reset(self):
        """
        Reset frame function and parameter set.
        """
        self._frame.reset()
        self._frame_args = ()
        self._frame_kwargs = {}
        self._frame_args_last = ()
        self._frame_kwargs_last = {}
        self._frame_func = None

    def set_frame_parameter(self, *args, **kwargs):
        """
        Set the parameters passed to the frame function..

        :param args: Positional arguments forwarded to the frame function.
        :param kwargs: Keyword arguments forwarded to the frame function.
        """
        self._frame_args = args
        self._frame_kwargs = kwargs

    def set_frame_function(self, func):
        """
        Set the function that builds the IO sequence.

        The function must accept an :class:`IoSyncFrame` as its first argument followed
        by any positional and/or keyword arguments defined in :meth:`set_frame_parameter`.

        :param func: Callable with signature ``func(frame, *args, **kwargs)``.
        """
        self._frame.reset()
        self._frame_func = func


    def _dicts_equal(self, d1, d2):
        if d1.keys() != d2.keys():
            return False

        for k in d1:
            v1, v2 = d1[k], d2[k]

            if isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
                if not np.array_equal(v1, v2):
                    return False
            elif isinstance(v1, dict) and isinstance(v2, dict):
                if not self._dicts_equal(v1, v2):
                    return False
            elif isinstance(v1, tuple) and isinstance(v2, tuple):
                if not self._tuples_equal(v1, v2):
                    return False
            else:
                if v1 != v2:
                    return False
        return True

    def _tuples_equal(self, t1, t2):
        if len(t1) != len(t2):
            return False

        for v1, v2 in zip(t1, t2):
            if isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
                if not np.array_equal(v1, v2):
                    return False
            elif isinstance(v1, tuple) and isinstance(v2, tuple):
                if not self._tuples_equal(v1, v2):
                    return False
            elif isinstance(v1, dict) and isinstance(v2, dict):
                if not self._dicts_equal(v1, v2):
                    return False
            else:
                if v1 != v2:
                    return False

        return True


    def _is_locked(self):
        return (self._frame._is_locked() and
                self._tuples_equal(self._frame_args, self._frame_args_last) and
                self._dicts_equal(self._frame_kwargs, self._frame_kwargs_last) and
                (self._frame_func is not None))

    def _get_instruction_list(self):
        if not self._is_locked():
            self._frame.reset()
            self._frame_func(self._frame, *copy.deepcopy(self._frame_args), **copy.deepcopy(self._frame_kwargs))
            self._frame_args_last = copy.deepcopy(self._frame_args)
            self._frame_kwargs_last = copy.deepcopy(self._frame_kwargs)
        return self._frame._get_instruction_list()

    def _get_acquisition_dict(self):
        return self._frame._get_acquisition_dict()

