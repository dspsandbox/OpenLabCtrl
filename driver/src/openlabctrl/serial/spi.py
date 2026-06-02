
from ..io.digital import DigitalIo


class SPI:
    """
    Bit-banged SPI master over a :class:`~openlabctrl.io.digital.DigitalIo` port.

    Supports all four SPI modes (CPOL × CPHA) and configurable pin assignment via
    single-bit masks. Call :meth:`io_config` once to initialize pin directions and idle
    states, then use :meth:`cs_low`, :meth:`write`, and :meth:`cs_high` to drive a
    transaction.

    :param io: :class:`~openlabctrl.io.digital.DigitalIo` instance used for bit-banging.
    :param clk_div: Clock divider relative to the frame clock. Must be a positive even integer ≥ 2.
        The SPI clock half-period is ``clk_div / 2`` frame clock cycles.
    :param cpol: Clock polarity. ``0`` = idle low, ``1`` = idle high.
    :param cpha: Clock phase. ``0`` = data sampled on leading edge, ``1`` = on trailing edge.
    :param sclk_mask: Single-bit mask selecting the SCLK pin.
    :param cs_mask: Single-bit mask selecting the CS pin, active-low.
    :param mosi_mask: Single-bit mask selecting the MOSI pin.
    :param miso_mask: Single-bit mask selecting the MISO pin.
    """
    def __init__(self, io: DigitalIo, clk_div: int, cpol: int, cpha: int, sclk_mask: int = 0b0001, cs_mask: int = 0b0010, mosi_mask: int = 0b0100, miso_mask: int = 0b1000):
        if type(io) != DigitalIo:
            raise Exception(f"SPI requires a DigitalIo instance for IO control. Got {type(io)} instead.")

        if clk_div < 2 or clk_div % 2 != 0:
            raise Exception("Clock divider must be a positive multiple of 2.")

        self._io = io
        self._clk_div = clk_div
        self._cpol = cpol
        self._cpha = cpha
        self._sclk_mask = sclk_mask
        self._cs_mask = cs_mask
        self._mosi_mask = mosi_mask
        self._miso_mask = miso_mask

    def io_config(self):
        """
        Configure pin directions and set all SPI signals to their idle state.

        Sets MISO as input and SCLK, CS, MOSI as outputs. SCLK is driven to its idle
        level (determined by ``cpol``), CS is deasserted (high), and MOSI is driven low.
        Call this once before the first transaction.
        """
        self._io.tristate(val=self._miso_mask, mask=0xf)
        clk = self._cpol * self._sclk_mask
        cs = self._cs_mask
        mosi = 0
        self._io.output(val=(clk | cs | mosi), mask=(self._sclk_mask | self._cs_mask | self._mosi_mask))

    def cs_low(self, wait: int = 1):
        """
        Assert chip select (drive CS low) and wait.

        :param wait: Number of half-clock periods to wait after asserting CS
            (actual delay = ``clk_div * wait`` frame clock cycles).
        """
        self._io.output(val=0, mask=self._cs_mask)
        self._io.delay(self._clk_div * wait)

    def cs_high(self, wait: int = 1):
        """
        Deassert chip select (drive CS high) after a settling delay.

        :param wait: Number of half-clock periods to wait before deasserting CS
            (actual delay = ``clk_div * wait`` frame clock cycles).
        """
        self._io.delay(self._clk_div * wait)
        self._io.output(val=self._cs_mask, mask=self._cs_mask)

    def write(self, data: int, size: int):
        """
        Transmit ``size`` bits of ``data`` MSB-first over MOSI.

        Clock edges follow the configured CPOL/CPHA mode. SCLK is returned to its
        idle level at the end of the transfer. CS must be asserted before calling
        this method (see :meth:`cs_low`).

        :param data: Integer value to transmit.
        :param size: Number of bits to transmit (starting from the MSB).
        """
        for i in range(size):
            mosi = ((data >> (size - 1 - i)) & 0x1) * self._mosi_mask
            clk = (self._cpol ^ self._cpha) * self._sclk_mask
            self._io.output(val=(mosi | clk), mask=(self._mosi_mask | self._sclk_mask))
            self._io.delay(self._clk_div // 2)
            clk ^= self._sclk_mask
            self._io.output(val=clk, mask=self._sclk_mask)
            self._io.delay(self._clk_div // 2)
        clk = self._cpol * self._sclk_mask
        self._io.output(val=clk, mask=self._sclk_mask)
