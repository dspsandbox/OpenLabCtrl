// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module xadc_output_routing #(
    parameter DATA_WIDTH = 16 
)(
    input clk,
    input resetn,
    
    input [DATA_WIDTH - 1 : 0] s_axis_tdata,
    input s_axis_tvalid,
    input [4 : 0] s_axis_tid,

    output [DATA_WIDTH - 1 : 0] xadc_vpn_tdata,
    output xadc_vpn_tvalid,

    output [DATA_WIDTH - 1 : 0] xadc_vaux0_tdata,
    output xadc_vaux0_tvalid,

    output [DATA_WIDTH - 1 : 0] xadc_vaux1_tdata,
    output xadc_vaux1_tvalid,

    output [DATA_WIDTH - 1 : 0] xadc_vaux8_tdata,
    output xadc_vaux8_tvalid,

    output [DATA_WIDTH - 1 : 0] xadc_vaux9_tdata,
    output xadc_vaux9_tvalid


);
    //see pages 45-47 of ug480 for the mapping of the TID to the XADC channel
    assign xadc_vpn_tdata = s_axis_tdata;
    assign xadc_vpn_tvalid = s_axis_tvalid && (s_axis_tid == 3);

    assign xadc_vaux0_tdata = s_axis_tdata;
    assign xadc_vaux0_tvalid = s_axis_tvalid && (s_axis_tid == 16);

    assign xadc_vaux1_tdata = s_axis_tdata;
    assign xadc_vaux1_tvalid = s_axis_tvalid && (s_axis_tid == 17);

    assign xadc_vaux8_tdata = s_axis_tdata;
    assign xadc_vaux8_tvalid = s_axis_tvalid && (s_axis_tid == 24);

    assign xadc_vaux9_tdata = s_axis_tdata;
    assign xadc_vaux9_tvalid = s_axis_tvalid && (s_axis_tid == 25);




endmodule