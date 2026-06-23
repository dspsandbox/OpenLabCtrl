// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module led #(
    parameter LED_WIDTH = 8,
    localparam INSTR_CMD_WIDTH = 4,
    localparam INSTR_DATA_WIDTH = 32,
    localparam VAL_OFFSET = 0,
    localparam MASK_OFFSET = 16
    
)(
    input clk,
    input resetn,
    input en,
    input instr_valid,
    input [INSTR_CMD_WIDTH-1:0] instr_cmd,
    input [INSTR_DATA_WIDTH-1:0] instr_data,
    output reg [LED_WIDTH-1:0] led_o

);
    //instruction commands
    localparam CMD_OUTPUT = 'h0;

    wire [LED_WIDTH-1:0] val;
    wire [LED_WIDTH-1:0] mask;

    assign val = instr_data[VAL_OFFSET + LED_WIDTH - 1 : VAL_OFFSET];
    assign mask = instr_data[MASK_OFFSET + LED_WIDTH - 1 : MASK_OFFSET];

    always @(posedge clk) begin
        if(resetn==0) begin
            led_o <= 0;
        end else begin
            if ((en == 1) && (instr_valid==1)) begin
                case(instr_cmd)
                    CMD_OUTPUT: begin
                        led_o <= (led_o & ~mask) | (val & mask);
                    end
    
                    default: begin
                        led_o <= led_o;
                    end
                endcase
            end else begin
                led_o <= led_o;
            end
        end
    end

endmodule