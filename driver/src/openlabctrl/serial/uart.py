from __future__ import annotations
from ..io.digital import DigitalIo


class UART:
    """
    Bit-banged UART transmitter over a :class:`~openlabctrl.io.digital.DigitalIo` port.

    Transmits standard UART frames (start bit + data bits LSB-first + optional parity + stop bits).
    TX is implemented open-drain: the output register is pre-loaded to ``0`` and the pin is toggled
    between driven-low (tristate=0) and high-Z (tristate=1). The internal pull-up resistors on the
    :class:`~openlabctrl.io.digital.DigitalIo` ports keep both TX and RX lines idle-high
    (mark state) without requiring external pull-ups.

    :param io: :class:`~openlabctrl.io.digital.DigitalIo` instance used for bit-banging.
    :param baud: Baud rate in bits per second. The bit period is derived from the IO clock frequency.
    :param data_len: Number of data bits per frame (default: 8).
    :param stop_len: Number of stop bits per frame (default: 1).
    :param parity: Parity mode. ``0`` = even, ``1`` = odd, ``None`` = no parity (default).
    :param tx_mask: Single-bit mask selecting the TX pin.
    :param rx_mask: Single-bit mask selecting the RX pin.
    """
    def __init__(self, io: DigitalIo, baud: int, data_len=8, stop_len=1, parity=None, tx_mask: int = 0b0001, rx_mask: int = 0b0010):
        if type(io) != DigitalIo:
            raise Exception(f"UART requires a DigitalIo instance for IO control. Got {type(io)} instead.")

        if parity not in [0, 1, None]:
            raise Exception(f"Parity must be 0 (even), 1 (odd), or None (no parity). Got {self._parity} instead.")

        self._io = io
        self._baud = baud
        self._data_len = data_len
        self._stop_len = stop_len
        self._parity = parity
        self._tx_mask = tx_mask
        self._rx_mask = rx_mask

    def io_config(self):
        """
        Configure pin directions and pre-load the TX output register.

        Sets both TX and RX to high-Z (idle/input mode) and pre-loads the TX output register
        to ``0`` so that driving TX low (start bit) is simply a matter of switching the pin
        to driven mode. Call this once before the first transmission.
        """
        self._io.tristate(val=(self._rx_mask | self._tx_mask), mask=(self._rx_mask | self._tx_mask))
        self._io.output(val=0, mask=self._tx_mask)

    def write(self, data: bytes | str):
        """
        Transmit one or more bytes over TX.

        Each byte is framed as: start bit (low), ``data_len`` data bits LSB-first, optional
        parity bit, and ``stop_len`` stop bits (high). Strings are UTF-8 encoded before
        transmission.

        :param data: Data to transmit. Accepts ``bytes`` or ``str``.
        """
        if not isinstance(data, (bytes, str)):
            raise Exception(f"UART write requires a bytes or str object. Got {type(data)} instead.")

        if isinstance(data, str):
            data = data.encode()

        t_bit = int(self._io._clk_freq / self._baud)

        for d in data:
            # Start bit
            self._io.tristate(val=0, mask=self._tx_mask)
            self._io.delay(t_bit)

            # Data bits (LSB first)
            for i in range(self._data_len):
                bit = ((d >> i) & 0x1) * self._tx_mask
                self._io.tristate(val=bit, mask=self._tx_mask)
                self._io.delay(t_bit)

            # Parity bit
            if self._parity is not None:
                parity_data = 0
                for i in range(self._data_len):
                    parity_data ^= ((d >> i) & 0x1)
                parity_bit = ((parity_data ^ self._parity) & 0x1) * self._tx_mask
                self._io.tristate(val=parity_bit, mask=self._tx_mask)
                self._io.delay(t_bit)

            # Stop bits
            self._io.tristate(val=self._tx_mask, mask=self._tx_mask)
            self._io.delay(t_bit * self._stop_len)
            
        