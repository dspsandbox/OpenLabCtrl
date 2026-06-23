// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module data_mux #(
    parameter DATA_WIDTH = 1
)(
    input wire [DATA_WIDTH-1:0] data_in_0,
    input wire [DATA_WIDTH-1:0] data_in_1,
    input wire sel,
    output wire [DATA_WIDTH-1:0] data_out

);
    assign data_out = sel ? data_in_1 : data_in_0;

endmodule