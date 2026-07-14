from openlabctrl.serial.spi import SPI


class ADF4351:
    """
    Driver for the Analog Devices ADF4351 wideband RF synthesizer (35 MHz - 4.4 GHz),
    bit-banged over two :class:`~openlabctrl.io.digital.DigitalIo` ports: one for the
    chip's control/status lines, one for its 3-wire SPI-like programming interface.

    Pin mapping:

    * digital_io_2[0] --> CE (chip enable)
    * digital_io_2[1] --> PDRF (RF output power-down, active high enables RF output)
    * digital_io_2[2] <-- MUXOUT (status mux output, e.g. lock detect / R or N divider)
    * digital_io_2[3] <-- LD (lock detect)
    * digital_io_3[0] --> CLK
    * digital_io_3[1] --> LE (latch enable)
    * digital_io_3[2] --> DATA

    :param frame: Device instance exposing ``digital_io_2`` and ``digital_io_3`` ports
        (see :class:`~openlabctrl.device.rp_125_14.Rp_125_14`).
    """

    def __init__(self, frame):
        self._frame = frame
        self._dio_ctrl = self._frame.digital_io_2
        self._dio_spi = self._frame.digital_io_3
        self._spi = SPI(io=self._dio_spi, clk_div=16, cpol=0, cpha=0)


    def io_config(self):
        """
        Configure pin directions on both ports and drive them to their idle state.

        """
        self._dio_ctrl.tristate(val=0b1100, mask=0b1111)
        self._spi.io_config()

    def _rsync(self):
        t_list = []
        io_list = [self._dio_ctrl, self._dio_spi]
        for io in io_list:
            t_list.append(io.get_time())
        t_max = max(t_list)
        for io in io_list:
            io.set_time(t_max)

    def _spi_write(self, data):
        self._spi.cs_low()
        self._spi.write(data=data, size=32)
        self._spi.cs_high()
        self._spi.cs_low()


    def chip_enable(self):
        """Drive CE high to power up the synthesizer."""
        self._dio_ctrl.output(val=0xf, mask=0b0001)
        self._rsync()

    def chip_disable(self):
        """Drive CE low to power down the synthesizer."""
        self._dio_ctrl.output(val=0x0, mask=0b0001)
        self._rsync()

    def rf_enable(self):
        """Drive PDRF high to enable the RF output stage."""
        self._dio_ctrl.output(val=0xf, mask=0b0010)
        self._rsync()

    def rf_disable(self):
        """Drive PDRF low to disable (power down) the RF output stage."""
        self._dio_ctrl.output(val=0x0, mask=0b0010)
        self._rsync()

    def frequency(self, val):
        """
        Program the synthesizer to output frequency ``val`` and latch registers 5-0.

        Computes the output divider (``RF_DIV_PWR2``), integer/fractional PLL
        feedback values (``INT``/``FRAC``/``MOD``) and the prescaler mode for the
        requested frequency, then writes all six ADF4351 registers in the
        required 5-4-3-2-1-0 order. The reference path is fixed at
        REFin = 25 MHz, R = 1, doubler/divide-by-2 disabled (D = T = 0), so
        PFD frequency = 25 MHz.

        :param val: Desired RF output frequency, in Hz. Must fall within
            [34.375 MHz, 4.4 GHz]
        """
        freq_vco_min = 2200e6
        freq_vco_max = 4400e6
        prescaler_threshold = 3300e6
        freq_out_min = freq_vco_min / 64
        freq_out_max = freq_vco_max
        freq_ref = 25e6
        D=0
        R=1
        T=0
        freq_pfd = freq_ref * (1 + D) / (R * (1 + T)) 
        rf_div_pwr2_min = 0
        rf_div_pwr2_max = 6

        
        if val < freq_out_min or val > freq_out_max:
            raise Exception(f"""Requested frequency {val/1e6:.3f} MHz out of range [{freq_out_min/1e6:.3f}, 
                            {freq_out_max/1e6:.3f}] MHz""")
        
        
        # Find the smallest output divider (2**RF_DIV_PWR2) that brings the VCO
        # back into its 2.2-4.4 GHz operating range for the requested output.
        for RF_DIV_PWR2 in range(rf_div_pwr2_min, rf_div_pwr2_max + 1):
            freq_vco = val * (2 ** RF_DIV_PWR2)
            if (freq_vco >= freq_vco_min) and (freq_vco <= freq_vco_max):
                break

        # PLL feedback divide ratio N = INT + FRAC/MOD (INT-N + fractional-N).
        N = freq_vco / freq_pfd
        INT = int(N)
        MOD = 4095
        FRAC = int((N - INT) * MOD)


        #REG 5: reserved bits + MUXOUT status LED pin mode (LD_PIN_MODE = digital lock detect)
        LD_PIN_MODE = 0b01
        self._spi_write(
            (0b00000000 << 24) |
            LD_PIN_MODE << 22 | 
            (0b0110000000000000000 << 3) |
            5
        )

        #REG 4 
        FB_SEL = 1
        BAND_SEL_CLK_DIV = 200
        VCO_PWR_DWN = 0
        MTLD = 0
        AUX_OUT_SEL = 0
        AUX_OUT_EN = 0
        AUX_OUT_PWR = 0
        RF_OUT_EN = 1
        RF_OUT_PWR = 0b11
        self._spi_write(
            (0b00000000 << 24) |
            (FB_SEL << 23) |
            (RF_DIV_PWR2 << 20) |
            (BAND_SEL_CLK_DIV << 12) |
            (VCO_PWR_DWN << 11) |
            (MTLD << 10) |
            (AUX_OUT_SEL << 9) |
            (AUX_OUT_EN << 8) | 
            (AUX_OUT_PWR << 6) |
            (RF_OUT_EN << 5) |
            (RF_OUT_PWR << 3) | 
            4
        )

        #REG 3
        CLK_MODE = 1
        ABP_WIDTH = 0
        CHARGE_CANCEL = 0
        CSR_EN = 0
        CLK_DIV_MODE = 0
        CLK_DIV_VAL = 0 
        self._spi_write(
            (0b00000000 << 24) |
            (CLK_MODE << 23) | 
            (ABP_WIDTH << 22) |
            (CHARGE_CANCEL << 21) |
            (0b00 << 19) |
            (CSR_EN << 18) | 
            (0b0 << 17) |
            (CLK_DIV_MODE << 15) |
            (CLK_DIV_VAL << 3) |
            3
        )

        #REG 2
        NOISE_MODE = 0
        MUXOUT_MODE = 0
        DOUBLE_BUF = 1
        CP = 7
        LDF = 0
        LDP =0
        PD_POL = 1
        PWR_DWN = 0
        CP_TRI = 0
        COUNTER_RST = 0

        self._spi_write(
            (0 << 31) |
            (NOISE_MODE << 29) |
            (MUXOUT_MODE << 26) |
            (D << 25) |
            (T << 24) |
            (R << 14) |
            (DOUBLE_BUF << 13) |
            (CP << 9) |
            (LDF << 8) |
            (LDP << 7) |
            (PD_POL << 6) |
            (PWR_DWN << 5) |
            (CP_TRI << 4) |
            (COUNTER_RST << 3) |
            2
        )
        
        #REG 1
        PHASE_ADJ = 0
        PRESCALER = int(val > prescaler_threshold)
        PHASE_VAL = 1

        self._spi_write(
                (0b000 << 29) |
                (PHASE_ADJ << 28) |
                (PRESCALER << 27) |
                (PHASE_VAL << 15) |
                (MOD << 3) |
                1
        )

        #REG 0 
        self._spi_write(
            (0 << 31) |
            (INT << 15) |
            (FRAC << 3) |
            0
        )
        
        #Rsync
        self._rsync()
        return
