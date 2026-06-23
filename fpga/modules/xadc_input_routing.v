// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module xadc_input_routing (
    input [3 : 0] vinn_i,
    input [3 : 0] vinp_i,

    output vauxn0,
    output vauxp0,
    output vauxn1,
    output vauxp1,
    output vauxn8,
    output vauxp8,
    output vauxn9,
    output vauxp9
);

    assign vauxn0 = vinn_i[1];
    assign vauxp0 = vinp_i[1];
    assign vauxn1 = vinn_i[2];
    assign vauxp1 = vinp_i[2];
    assign vauxn8 = vinn_i[0];
    assign vauxp8 = vinp_i[0];
    assign vauxn9 = vinn_i[3];
    assign vauxp9 = vinp_i[3];
    
endmodule