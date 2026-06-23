// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module instr_mux #(
    localparam INSTR_WIDTH = 64,
    localparam INSTR_ADDR_LSB = 60,
    localparam INSTR_ADDR_MSB = 63
) (
    input clk,
    input resetn,
    
    input [INSTR_WIDTH-1:0] S00_AXIS_tdata,
    input S00_AXIS_tvalid,
    output S00_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M00_AXIS_tdata,
    output M00_AXIS_tvalid,
    input M00_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M01_AXIS_tdata,
    output M01_AXIS_tvalid,
    input M01_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M02_AXIS_tdata,
    output M02_AXIS_tvalid,
    input M02_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M03_AXIS_tdata,
    output M03_AXIS_tvalid,
    input M03_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M04_AXIS_tdata,
    output M04_AXIS_tvalid,
    input M04_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M05_AXIS_tdata,
    output M05_AXIS_tvalid,
    input M05_AXIS_tready,    

    output  [INSTR_WIDTH-1:0] M06_AXIS_tdata,
    output M06_AXIS_tvalid,
    input M06_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M07_AXIS_tdata,
    output M07_AXIS_tvalid,
    input M07_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M08_AXIS_tdata,
    output M08_AXIS_tvalid,
    input M08_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M09_AXIS_tdata,
    output M09_AXIS_tvalid,
    input M09_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M10_AXIS_tdata,
    output M10_AXIS_tvalid,
    input M10_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M11_AXIS_tdata,
    output M11_AXIS_tvalid,
    input M11_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M12_AXIS_tdata,
    output M12_AXIS_tvalid,
    input M12_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M13_AXIS_tdata,
    output M13_AXIS_tvalid,
    input M13_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M14_AXIS_tdata,
    output M14_AXIS_tvalid,
    input M14_AXIS_tready,

    output  [INSTR_WIDTH-1:0] M15_AXIS_tdata,
    output M15_AXIS_tvalid,
    input M15_AXIS_tready
);


    wire [INSTR_ADDR_MSB-INSTR_ADDR_LSB:0] addr;
    assign addr = S00_AXIS_tdata[INSTR_ADDR_MSB:INSTR_ADDR_LSB];
    
    assign M00_AXIS_tdata = S00_AXIS_tdata;
    assign M00_AXIS_tvalid = S00_AXIS_tvalid && (addr == 0);
    
    assign M01_AXIS_tdata = S00_AXIS_tdata;
    assign M01_AXIS_tvalid = S00_AXIS_tvalid && (addr == 1);

    assign M02_AXIS_tdata = S00_AXIS_tdata;
    assign M02_AXIS_tvalid = S00_AXIS_tvalid && (addr == 2);

    assign M03_AXIS_tdata = S00_AXIS_tdata;
    assign M03_AXIS_tvalid = S00_AXIS_tvalid && (addr == 3);

    assign M04_AXIS_tdata = S00_AXIS_tdata;
    assign M04_AXIS_tvalid = S00_AXIS_tvalid && (addr == 4);

    assign M05_AXIS_tdata = S00_AXIS_tdata;
    assign M05_AXIS_tvalid = S00_AXIS_tvalid && (addr == 5);

    assign M06_AXIS_tdata = S00_AXIS_tdata;
    assign M06_AXIS_tvalid = S00_AXIS_tvalid && (addr == 6);

    assign M07_AXIS_tdata = S00_AXIS_tdata;
    assign M07_AXIS_tvalid = S00_AXIS_tvalid && (addr == 7);

    assign M08_AXIS_tdata = S00_AXIS_tdata;
    assign M08_AXIS_tvalid = S00_AXIS_tvalid && (addr == 8);

    assign M09_AXIS_tdata = S00_AXIS_tdata;
    assign M09_AXIS_tvalid = S00_AXIS_tvalid && (addr == 9);

    assign M10_AXIS_tdata = S00_AXIS_tdata;
    assign M10_AXIS_tvalid = S00_AXIS_tvalid && (addr == 10);

    assign M11_AXIS_tdata = S00_AXIS_tdata;
    assign M11_AXIS_tvalid = S00_AXIS_tvalid && (addr == 11);

    assign M12_AXIS_tdata = S00_AXIS_tdata;
    assign M12_AXIS_tvalid = S00_AXIS_tvalid && (addr == 12);

    assign M13_AXIS_tdata = S00_AXIS_tdata;
    assign M13_AXIS_tvalid = S00_AXIS_tvalid && (addr == 13);

    assign M14_AXIS_tdata = S00_AXIS_tdata;
    assign M14_AXIS_tvalid = S00_AXIS_tvalid && (addr == 14);

    assign M15_AXIS_tdata = S00_AXIS_tdata;
    assign M15_AXIS_tvalid = S00_AXIS_tvalid && (addr == 15);

    assign S00_AXIS_tready = (addr == 0) ? M00_AXIS_tready :
                             (addr == 1) ? M01_AXIS_tready :
                             (addr == 2) ? M02_AXIS_tready :
                             (addr == 3) ? M03_AXIS_tready :
                             (addr == 4) ? M04_AXIS_tready :
                             (addr == 5) ? M05_AXIS_tready :
                             (addr == 6) ? M06_AXIS_tready :
                             (addr == 7) ? M07_AXIS_tready :
                             (addr == 8) ? M08_AXIS_tready :
                             (addr == 9) ? M09_AXIS_tready :
                             (addr == 10) ? M10_AXIS_tready :
                             (addr == 11) ? M11_AXIS_tready :
                             (addr == 12) ? M12_AXIS_tready :
                             (addr == 13) ? M13_AXIS_tready :
                             (addr == 14) ? M14_AXIS_tready :
                             (addr == 15) ? M15_AXIS_tready :
                             1'b0;




    
endmodule