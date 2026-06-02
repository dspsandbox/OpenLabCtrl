import numpy as np
import copy
from .frame import IoSyncFrame, ParamIoSyncFrame
from .io.sync import TriggerSource
from .device.rp_base import Rp_base


class IoSequence():
    """
    Multi-device IO sequence.

    An :class:`IoSequence` coordinates a list of devices by assigning frames to each
    one and optionally inserting synchronization barriers (:meth:`add_rsync`) between
    them. Once all frames are added, :meth:`upload` transfers the instruction lists to
    the devices and :meth:`start` begins execution.

    :param device_list: List of device instances involved in this IO Sequence.
    """
    def __init__(self, device_list):
        self._rsync_label_list= []
        self._device_dict = {}
        for device in device_list:
            device_uid = device.get_uid()
            if device_uid in self._device_dict:
                raise Exception(f"Device {device_uid} already exists in sequence. Please make sure all devices in the device list have unique UIDs.")
            self._device_dict[device_uid] = device
            
    
    
    def reset(self):
        """
        Remove scheduled frames and rsync events. 
        """
        self._check_sequence_done()
        self._rsync_label_list = []
        for device in self._device_dict.values():
            device._reset()


    def add_frame(self, frame, device, label=None):
        """
        Assign a frame to a device in the sequence.

        :param frame: :class:`~openlabctrl.frame.IoSyncFrame` or
            :class:`~openlabctrl.frame.ParamIoSyncFrame` to add.
        :param device: Target device instance. Must be in the sequence device list and
            compatible with the frame's device type.
        :param label: Optional label for the frame. Auto-generated if not provided.
        """
        self._check_sequence_done()
        if (type(frame) is not IoSyncFrame) and (type(frame) is not ParamIoSyncFrame):
             raise Exception(f"Frame must be of type IoSyncFrame or ParamIoSyncFrame, got {type(frame)}.")
        if not issubclass(type(device), Rp_base):
                raise Exception(f"Provided device attribute is not a valid device instance.")
        if not isinstance(device, frame._device_type) and frame._device_type not in device.COMPATIBLE_DEVICES:
            raise Exception(f"Provided device ({device.get_uid()}) is neither an instance of the frame device class ({frame._device_type.__name__}) nor within its compatible devices ({', '.join([cls.__name__ for cls in frame._device_type.COMPATIBLE_DEVICES])}).")
        if device not in self._device_dict.values():
            raise Exception(f"Provided device ({device.get_uid()}) is not in the sequence device list.")

        device._add_frame(frame, label)


    def add_rsync(self):
        """
        Insert a synchronization barrier across all devices (requires a daisy chain / sync connection between devices).
        All devices wait at this barrier until the slowest one arrives before proceeding to the next frame.
        """
        self._check_sequence_done()
        label = f"rsync_{len(self._rsync_label_list)}"
        for device in self._device_dict.values():
            device._add_frame(IoSyncFrame(device_type=type(device), trig=TriggerSource._SYNC_DAISY_CHAIN), label=label)
        self._rsync_label_list.append(label)


    def sequence_description(self):
        """
        Return an ASCII table showing the frame layout across all devices.

        Rsync barriers are shown as horizontal lines spanning all columns. Frames
        triggered by an external source are marked with ``(*)``.

        :rtype: str
        """
        width_max = 0
        for device_uid in self._device_dict.keys():
            device = self._device_dict[device_uid]
            width = max(len(frame_label) for frame_label in device._frame_dict.keys()) if len(device._frame_dict) > 0 else 0
            width_max = max([width_max, width, len(device_uid)])
        
        padding = 1
        width_max += 2*padding
        description = ""
        description += "+"  +("-" * width_max + "+") * len(self._device_dict) + "\n"
        device_uid_list = list(self._device_dict.keys())
        for i in range(len(device_uid_list)):
            device_uid = device_uid_list[i]
            device = self._device_dict[device_uid]
            description += "|"
            description += " " * padding
            description += device_uid
            description += (width_max - len(device_uid) - padding) * " "
        description += "|"
        description += "\n"
        description += "+" + ("-" * width_max + "+") * len(self._device_dict) + "\n"
        
        
        idx_dict = {}
        idx_dict["rsync"] = 0

        frame_label_dict = {}
        for device_uid in self._device_dict.keys():
            device = self._device_dict[device_uid]
            frame_label_dict[device_uid] = [(f"{label} (*)" if device._frame_dict[label]._trig in [TriggerSource.EXT_HIGH, TriggerSource.EXT_LOW, TriggerSource.EXT_RISE, TriggerSource.EXT_FALL, TriggerSource.EXT_RISE_FALL] else label) for label in device._frame_dict.keys()]
            

        for rsync_label in self._rsync_label_list:
            idx_rsync_max = max(frame_label_list.index(rsync_label) for frame_label_list in frame_label_dict.values())
            for device_uid in self._device_dict.keys():
                idx_sync = frame_label_dict[device_uid].index(rsync_label)
                for i in range(idx_rsync_max - idx_sync):
                    frame_label_dict[device_uid].insert(idx_sync, "")
        
        description_len = max(len(frame_label_dict[device_uid]) for device_uid in frame_label_dict.keys())
        
        for i in range(description_len):
            description += "|"
            for device_uid in frame_label_dict.keys():

                labels = frame_label_dict[device_uid]
                if i < len(labels):
                    label = labels[i]
                else:
                    label = ""
                if label in self._rsync_label_list:
                    padding_char = "-"
                    separator_char = "-"
                else:
                    padding_char = " "
                    separator_char = "|"
                description += padding_char * padding
                description += label
                description += (width_max - len(label) - padding) * padding_char
                if device_uid != list(frame_label_dict.keys())[-1]:
                    description += separator_char
                
            
            description += "|"
            description += "\n"
        description += "+" + ("-" * width_max + "+") * len(self._device_dict) + "\n"
        description += "NOTE: Frames with (*) are triggered by external trigger source.\n"
        
        return description

    def upload(self):
        """
        Upload all frames to their respective devices.

        Compiles and transfers the instruction lists for every device in the sequence.
        Must be called after all frames (and rsync barriers) have been added, and before
        :meth:`start`.
        """
        self._check_sequence_done()
        for device in self._device_dict.values():
            device._upload()


    def _check_sequence_done(self, autostop=True):
        status = self.get_status()
        done = all(device_status["done"] for device_status in status.values())
        enabled = any(device_status["enabled"] for device_status in status.values())
        if enabled and not done:
            raise Exception("Sequence is not finished, please stop it first")
        
        if enabled and done and autostop:
            self.stop()

    def start(self):
        """
        Start execution of the uploaded sequence on all devices simultaneously.
        """
        self._check_sequence_done()
        for device in self._device_dict.values():
            device._start()

    def is_done(self):
        """
        Return ``True`` if all devices have finished executing their frames.

        :rtype: bool
        """
        return all(device_status["done"] for device_status in self.get_status().values())

    def is_error(self):
        """
        Return ``True`` if any device has reported an error.

        :rtype: bool
        """
        return any(device_status["error"] for device_status in self.get_status().values())

    def wait(self):
        """
        Block until the sequence has finished executing.

        Polls :meth:`is_done` in a tight loop. Raises an exception if any device
        reports an error while waiting.

        """
        while not self.is_done():
            if self.is_error():
                raise Exception("Sequence error, please check state")

    def stop(self):
        """
        Stop execution on all devices.
        """
        for device in self._device_dict.values():
            device._stop()

    def get_status(self):
        """
        Return the execution status of all devices. See :doc:`/examples/00_led_blink` for an example of status messages.

        :rtype: dict
        """
        status_dict = {}
        for device_uid, device in self._device_dict.items():
            status_dict[device_uid] = device._get_status()
        return status_dict

    def get_scope(self):
        """
        Retrieve acquisition data from all devices after the sequence has finished.
        See :doc:`/examples/04_rf_in_out` for and example of scope dictionaries and acquired data.

        :rtype: dict
        """
        scope_dict = {}
        for device_uid, device in self._device_dict.items():
            scope_dict[device_uid] = device._get_scope()
        return scope_dict     
    
