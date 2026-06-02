"""
Simplified DMA engine driver adapted from https://github.com/Xilinx/PYNQ/blob/master/pynq/lib/dma.py
"""

DMA_TYPE_TX = 1
DMA_TYPE_RX = 0

class _SDMAChannel:
    def __init__(self, addr, tx_rx, tcp_ctrl_client):

        self._tcp_ctrl_client = tcp_ctrl_client
        self._first_transfer = True
        self._tx_rx = tx_rx

        if tx_rx == DMA_TYPE_RX:
            self._offset = 0x30 + addr
        else:
            self._offset = addr

        self.transferred = 0
        self.start()

    @property
    def running(self):
        """True if the DMA engine is currently running"""
        return self._tcp_ctrl_client.read(self._offset + 4) & 0x01 == 0x00

    @property
    def idle(self):
        """True if the DMA engine is idle

        `transfer` can only be called when the DMA is idle

        """
        return self._tcp_ctrl_client.read(self._offset + 4) & 0x02 == 0x02

    @property
    def error(self):
        """True if DMA engine is in an error state"""
        return self._tcp_ctrl_client.read(self._offset + 4) & 0x70 != 0x0

    def start(self):
        """Start the DMA engine if stopped"""
        self._tcp_ctrl_client.write(self._offset, 0x0001)
        while not self.running:
            pass
        self._first_transfer = True

    def stop(self):
        """Stops the DMA channel and aborts the current transfer"""
        self._tcp_ctrl_client.write(self._offset, 0x0004)
        self._tcp_ctrl_client.write(self._offset, 0x0000)
        while self.running:
            pass

    def transfer(self, addr_start, nbytes):
        """Start a DMA transfer from/to the given physical address with the given number of bytes"""
        if not self.running:
            raise RuntimeError("DMA channel not started")
        if not self.idle and not self._first_transfer:
            raise RuntimeError("DMA channel not idle")

       
        self.transferred = 0
        self._tcp_ctrl_client.write(
            self._offset + 0x18, (addr_start) & 0xFFFFFFFF
        )
        self._tcp_ctrl_client.write(
            self._offset + 0x1C, ((addr_start) >> 32) & 0xFFFFFFFF
        )
        self._tcp_ctrl_client.write(self._offset + 0x28, nbytes)
        self._first_transfer = False

    def delay(self):
        """Wait for the transfer to complete"""
        if not self.running:
            raise RuntimeError("DMA channel not started")
        while True:
            error = self._tcp_ctrl_client.read(self._offset + 4)
            if self.error:
                if error & 0x10:
                    raise RuntimeError("DMA Internal Error (transfer length 0?)")
                if error & 0x20:
                    raise RuntimeError(
                        "DMA Slave Error (cannot access memory map interface)"
                    )
                if error & 0x40:
                    raise RuntimeError("DMA Decode Error (invalid address)")
            if self.idle:
                break
        self.transferred = self._tcp_ctrl_client.read(self._offset + 0x28)


class DMA():
    def __init__(self, addr, tcp_ctrl_client):
        self.sendchannel = _SDMAChannel(addr, DMA_TYPE_TX, tcp_ctrl_client)
        self.recvchannel = _SDMAChannel(addr, DMA_TYPE_RX, tcp_ctrl_client)
        