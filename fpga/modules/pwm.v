// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module pwm #(
    parameter DUTY_CYCLE_WIDTH = 8,
    localparam INSTR_CMD_WIDTH = 4,
    localparam INSTR_DATA_WIDTH = 32
    
)(
    input clk,
    input resetn,
    input en,
    input instr_valid,
    input [INSTR_CMD_WIDTH-1:0] instr_cmd,
    input [INSTR_DATA_WIDTH-1:0] instr_data,
    output reg [DUTY_CYCLE_WIDTH-1:0] duty_cycle
);
    //instruction commands
    localparam CMD_DUTY_CYCLE = 'h0;

    always @(posedge clk) begin
        if(resetn==0) begin
            duty_cycle <= 0;
        end else begin
            if ((en == 1) && (instr_valid==1)) begin
                case(instr_cmd)
                    CMD_DUTY_CYCLE: begin
                        duty_cycle <= instr_data[DUTY_CYCLE_WIDTH-1:0];
                    end
                    default: begin
                        duty_cycle <= duty_cycle;
                    end
                endcase
            end else begin
                duty_cycle <= duty_cycle;
            end
        end
    end

endmodule