// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module iobuf_array #(
    parameter PORT_WIDTH = 1
)
(
    input wire [PORT_WIDTH-1:0] buf_t,
    input  wire [PORT_WIDTH-1:0] buf_o,
    output wire [PORT_WIDTH-1:0] buf_i,
    inout  wire [PORT_WIDTH-1:0] buf_io
);

genvar i;
generate
    for (i = 0; i < PORT_WIDTH; i = i + 1) begin : gen_iobuf
        IOBUF iobuf_inst (
            .O(buf_i[i]),
            .T(buf_t[i]),
            .I(buf_o[i]),
            .IO(buf_io[i])
        );
    end
endgenerate

endmodule