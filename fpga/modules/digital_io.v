// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module digital_io #(
    parameter IO_WIDTH = 4,
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
    output reg [IO_WIDTH-1:0] io_t,
    output reg [IO_WIDTH-1:0] io_o

);
    //instruction commands
    localparam CMD_OUTPUT = 'h0, CMD_TRISTATE = 'h1;

    wire [IO_WIDTH-1:0] val;
    wire [IO_WIDTH-1:0] mask;

    assign val = instr_data[VAL_OFFSET + IO_WIDTH - 1 : VAL_OFFSET];
    assign mask = instr_data[MASK_OFFSET + IO_WIDTH - 1 : MASK_OFFSET];

    always @(posedge clk) begin
        if(resetn==0) begin
            io_o <= 0;
            io_t <= {IO_WIDTH{1'b1}}; //tristate by default
        end else begin
            if ((en == 1) && (instr_valid==1)) begin
                case(instr_cmd)
                    CMD_OUTPUT: begin
                        io_o <= (io_o & ~mask) | (val & mask);
                        io_t <= io_t;
                    end
                    CMD_TRISTATE: begin
                        io_o <= io_o;
                        io_t <= (io_t & ~mask) | (val & mask);
                    end
                    default: begin
                        io_o <= io_o;
                        io_t <= io_t;
                    end
                endcase
            end else begin
                io_o <= io_o;
                io_t <= io_t;
            end
        end
    end

endmodule