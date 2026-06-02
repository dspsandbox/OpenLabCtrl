import time
from pathlib import Path
import numpy as np
from zynq_tcp_ctrl import ZynqTcpCtrlClient
from ..frame import IoSyncFrame, ParametrizedIoSyncFrame
from ..dma.dma import DMA


class Rp_base():
    """
    Base class for Red Pitaya devices. 

    :param ip: IP address or URL
    :param label: User-defined name
    :param daisy_0_en: Enable daisy chain sync connector 0
    :param daisy_1_en: Enable daisy chain sync connector 1
    :param force: Force bitstream reloading (resets FPGA configuration)
    """
    def __init__(self, ip: str, label: str, daisy_0_en: bool, daisy_1_en: bool, force: bool):
        self._ip = ip
        self._label = label
        self._check_attribute("CLK_FREQ")
        self._check_attribute("IO_DICT")
        self._check_attribute("MMAP_DICT")
        self._check_attribute("ADDR_DICT")
        self._check_attribute("BITSTREAM")
        self._check_attribute("COMPATIBLE_DEVICES")
        
        self._tcp_ctrl_client = None
        self._init_tcp_ctrl_client()
        self._init_mmap()

        self._load_bitstream(force=force)

        self._frame_dict = {}
        self._ptr_dict = {} 
        self._dma_dict = {}
        self._init_ptr()
        self._init_dma()
        self._init_daisy(daisy_0_en, daisy_1_en)
        
        self._stop()


    def _init_daisy(self, daisy_0_en, daisy_1_en):
        self._tcp_ctrl_client.write(addr=self.ADDR_DICT["reg_bank_daisy_0_sel"], val=not(daisy_0_en))
        self._tcp_ctrl_client.write(addr=self.ADDR_DICT["reg_bank_daisy_1_sel"], val=not(daisy_1_en))
    
    def _init_mmap(self):
        self._mmap_dict = {}
        for mmap_name in self.MMAP_DICT.keys():
            addr = self.MMAP_DICT[mmap_name]["addr"]
            size = self.MMAP_DICT[mmap_name]["size"]
            self._tcp_ctrl_client.add_mmap_region(addr=addr, size=size)
    def _init_tcp_ctrl_client(self):
        self._tcp_ctrl_client = ZynqTcpCtrlClient(self._ip)

    def _init_ptr(self):
        self._ptr_dict["instr"] = self.MMAP_DICT["mem_instr"]["addr"]
        for io_name in self.IO_DICT.keys():
            if "scope" in io_name:
                self._ptr_dict[io_name] = self.MMAP_DICT[f"mem_{io_name}"]["addr"]

    def _init_dma(self):
        DMA_MARKER = "dma_"
        for addr_name in self.ADDR_DICT.keys():
            if addr_name.startswith(DMA_MARKER) and ("instr" in addr_name or "scope" in addr_name):
                key = addr_name[len(DMA_MARKER):]
                self._dma_dict[key] = DMA(addr=self.ADDR_DICT[f"dma_{key}"], tcp_ctrl_client=self._tcp_ctrl_client)


    def _check_attribute(self, attr):
        if not hasattr(self, attr):
            raise Exception(f"Attribute {attr} not found. Please define {attr} in the device subclass.")

    def _load_bitstream(self, force=False):
        path = Path(__file__).parent.parent / self.BITSTREAM
        self._tcp_ctrl_client.load_bitstream(path=str(path), force=force)
        
    def _reset(self):
        self._stop()
        self._frame_dict = {}
        self._init_ptr()
    

    def _add_frame(self, frame, label=None):
        if (type(frame) is not IoSyncFrame) and (type(frame) is not ParametrizedIoSyncFrame):
            raise Exception(f"Frame must be of type IoSyncFrame or ParametrizedIoSyncFrame. Got {type(frame)}.")
        if label is None:
            label = f"frame_{len(self._frame_dict)}"
        if label in self._frame_dict:
            raise Exception(f"Frame label {label} already exists in device {self.get_uid()}. Please provide a unique label for each frame.")
        self._frame_dict[label] = frame

        
            
    def _upload(self, ):
        frame_dict = self._frame_dict
        self._reset()
        for label in frame_dict.keys():
            frame = frame_dict[label]
            instr_list = frame._get_instruction_list()
    
            #Check instruction memory size
            instr_list_bytes = instr_list.tobytes()
            instr_list_size = len(instr_list_bytes)
            if self._ptr_dict["instr"] + instr_list_size > self.MMAP_DICT["mem_instr"]["addr"] + self.MMAP_DICT["mem_instr"]["size"]:
                raise Exception(f"Frame {label} ({self.get_uid()}) exceeds available instruction memory ({self.MMAP_DICT['mem_instr']['size']} bytes).")
            
            #Check scope memory size
            acq_dict = frame._get_acquisition_dict()
            for scope_label in acq_dict.keys():
                for acq_label in acq_dict[scope_label].keys():
                    acq_samples = acq_dict[scope_label][acq_label]["samples"]
                    acq_size = acq_samples * np.int16().nbytes  
                    if (self._ptr_dict[scope_label] + acq_size) > (self.MMAP_DICT[f"mem_{scope_label}"]["addr"] + self.MMAP_DICT[f"mem_{scope_label}"]["size"]):
                        raise Exception(f"Frame {label} ({self.get_uid()}) exceeds available {scope_label} memory ({self.MMAP_DICT[f'mem_{scope_label}']['size']} bytes).")
            
            #Transfer frame instruction list to device
            self._tcp_ctrl_client.write(addr=self._ptr_dict["instr"], val=instr_list_bytes)

            #Append frame metadata
            self._frame_dict[label] = frame
            self._ptr_dict["instr"] += instr_list_size
            for scope_label in acq_dict.keys():
                for acq_label in acq_dict[scope_label].keys():
                    acq_dict[scope_label][acq_label]["addr"] = self._ptr_dict[scope_label]
                    self._ptr_dict[scope_label] += acq_dict[scope_label][acq_label]["samples"] * np.int16().nbytes 


        

    def _parse_err(self, err_code):
        io_name_list_with_err = []
        for io_name in self.IO_DICT.keys():
            io_addr = self.IO_DICT[io_name]["addr"]

            if err_code == (1 << io_addr):
                io_name_list_with_err.append(io_name)
        
        if len(io_name_list_with_err) == 0:
            return None
        else:
            return f"Error in IO(s): {', '.join(io_name_list_with_err)}"    
        

    def _get_status(self):
        en = bool(self._tcp_ctrl_client.read(addr=self.ADDR_DICT["reg_bank_en"]))
        sync_counter = self._tcp_ctrl_client.read(addr=self.ADDR_DICT["reg_bank_sync_counter"])
        err_code = self._tcp_ctrl_client.read(addr=self.ADDR_DICT["reg_bank_err"])
        done_code = self._tcp_ctrl_client.read(addr=self.ADDR_DICT["reg_bank_done"])
        frame_label_list = list(self._frame_dict.keys())
        frame_label = frame_label_list[sync_counter - 1] if sync_counter > 0 else None
        io_status = {}
        for io_name in self.IO_DICT.keys():
            if io_name[0] != "_":
                io_status[io_name] = {}
                io_status[io_name]["error"] = bool(err_code & (1 << self.IO_DICT[io_name]["addr"]))
                io_status[io_name]["done"] = bool(done_code & (1 << self.IO_DICT[io_name]["addr"]))

        err = any(io_status[io_name]["error"] for io_name in io_status.keys())
        if len(frame_label_list) == 0:
            done = False
        else:
            done = ((frame_label == frame_label_list[-1]) and 
                        all(io_status[io_name]["done"] for io_name in io_status.keys()) and 
                        not any(io_status[io_name]["error"] for io_name in io_status.keys()))
        status = {
            "enabled": en,
            "done": done,
            "error": err,
            "current_frame": frame_label,
            "io": io_status
        }
        return status


    def _start(self):
        if len(self._frame_dict) == 0:
            raise Exception("No frames uploaded. Please add at least one frame before starting the device.")
        pass
        
        status = self._get_status()
        if status["enabled"] and not status["done"]:
            raise Exception("Device is already running. Please stop the device before starting it again.")
             
        #Start dma
        for key in self._dma_dict.keys():
            if "scope" in key:
                dma_ch = self._dma_dict[key].recvchannel
            elif "instr" in key:
                dma_ch = self._dma_dict[key].sendchannel
            nbytes = self._ptr_dict[key] - self.MMAP_DICT[f"mem_{key}"]["addr"]
            if nbytes > 0:
                dma_ch.transfer(addr_start=self.MMAP_DICT[f"mem_{key}"]["addr"], nbytes=nbytes)    
        
        #Set stream ctrl of scopes
        for key in self._dma_dict.keys():
            if "scope" in key:
                nbytes = self._ptr_dict[key] - self.MMAP_DICT[f"mem_{key}"]["addr"]
                self._tcp_ctrl_client.write(addr=self.ADDR_DICT[f"reg_bank_{key}_samples"], val=nbytes//2) 
        
        #Assert enable bit
        self._tcp_ctrl_client.write(addr=self.ADDR_DICT["reg_bank_en"], val=0x1)

        

    def _stop(self):
        #Reset DMA
        for key in self._dma_dict.keys():
            if "scope" in key:
                dma_ch = self._dma_dict[key].recvchannel
            elif "instr" in key:
                dma_ch = self._dma_dict[key].sendchannel
            dma_ch.stop()
            dma_ch.start()

        #Deassert enable bit
        self._tcp_ctrl_client.write(addr=self.ADDR_DICT["reg_bank_en"], val=0x0)

        #Flush fifos
        self._tcp_ctrl_client.write(addr=self.ADDR_DICT["reg_bank_flush"], val=0x1)
        time.sleep(1e-3)
        self._tcp_ctrl_client.write(addr=self.ADDR_DICT["reg_bank_flush"], val=0x0)
        return
    
    def get_uid(self) -> str:
        """
        Return a unique device identifier of the form ``<label>@<ip>``, e.g. ``my_rp@192.168.1.100``.

        """
        uid = f"{self._label}@{self._ip}"
        return uid

    def _get_scope(self):
        scope_dict = {}
        for frame_label in self._frame_dict.keys():
            scope_dict[frame_label] = {}
            frame = self._frame_dict[frame_label]
            acq_dict = frame._get_acquisition_dict()
            
            for scope_label in acq_dict.keys():
                scope_dict[frame_label][scope_label] = {}
                for acq_label in acq_dict[scope_label].keys():
                    addr = acq_dict[scope_label][acq_label]["addr"]
                    samples = acq_dict[scope_label][acq_label]["samples"]
                    t = acq_dict[scope_label][acq_label]["t"]
                    src = acq_dict[scope_label][acq_label]["src"]
                    dec = acq_dict[scope_label][acq_label]["dec"]
                    data = self._tcp_ctrl_client.read(addr=addr, size=(samples), dtype=np.int16)
                    scope_dict[frame_label] [scope_label][acq_label] = {"t": t, "src": src, "dec": dec, "samples": samples, "data": data}
        return scope_dict
    

