// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module sdm #(
    parameter DUTY_CYCLE_WIDTH = 12
)(
input clk, 
input resetn,
input [DUTY_CYCLE_WIDTH-1 : 0] duty_cycle,
output sdm_o);


reg [DUTY_CYCLE_WIDTH : 0] accumulator;
always @(posedge clk) begin
    if (resetn == 0) begin
        accumulator <= 0;
    end else begin    
        accumulator <= accumulator[DUTY_CYCLE_WIDTH-1:0] + duty_cycle;
    end 
end 
assign sdm_o = accumulator[DUTY_CYCLE_WIDTH];
endmodule
