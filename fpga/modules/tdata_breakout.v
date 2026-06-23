// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module tdata_breakout #(
    parameter DATA_WIDTH = 32
)(
    input clk,
    input resetn,
    input S00_AXIS_tvalid,
    input [DATA_WIDTH-1:0] S00_AXIS_tdata,
    input [DATA_WIDTH-1:0] S00_AXIS_tlast,
    output S00_AXIS_tready,

    output M00_AXIS_tvalid,
    output [DATA_WIDTH-1:0] M00_AXIS_tdata,
    output [DATA_WIDTH-1:0] M00_AXIS_tlast,
    input M00_AXIS_tready,

    output[DATA_WIDTH-1:0] tdata
);

    reg [DATA_WIDTH-1:0] tdata_reg;

    always @(posedge clk) begin
        if(resetn == 0) begin
            tdata_reg <= 0;
        end else begin
            if(S00_AXIS_tvalid == 1) begin
                tdata_reg <= S00_AXIS_tdata;
            end else begin
                tdata_reg <= tdata_reg;
            end
        end
    end

    assign S00_AXIS_tready = M00_AXIS_tready;
    assign M00_AXIS_tvalid = S00_AXIS_tvalid;
    assign M00_AXIS_tdata = S00_AXIS_tdata;
    assign M00_AXIS_tlast = S00_AXIS_tlast;
    assign tdata = S00_AXIS_tvalid ? S00_AXIS_tdata : tdata_reg;

    endmodule