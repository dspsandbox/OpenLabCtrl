// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module scope#(
    parameter DATA_00_WIDTH = 32,
    parameter DATA_01_WIDTH = 32,
    parameter DATA_02_WIDTH = 32,
    parameter DATA_03_WIDTH = 32,
    parameter DATA_04_WIDTH = 32,
    parameter DATA_05_WIDTH = 32,
    parameter DATA_06_WIDTH = 32,
    parameter DATA_07_WIDTH = 32,
    parameter DATA_08_WIDTH = 32,
    parameter DATA_09_WIDTH = 32,
    parameter DATA_10_WIDTH = 32,
    parameter DATA_11_WIDTH = 32,
    parameter DATA_12_WIDTH = 32,
    parameter DATA_13_WIDTH = 32,
    parameter DATA_14_WIDTH = 32,
    parameter DATA_15_WIDTH = 32,
    
    localparam INSTR_CMD_WIDTH = 4,
    localparam INSTR_DATA_WIDTH = 32,
    localparam SCOPE_WIDTH = 16,
    localparam SAMPLES_WIDTH = 32,
    localparam DEC_WIDTH = 32

)(
    input clk,
    input resetn,
    input en,
    input instr_valid,
    input [INSTR_CMD_WIDTH-1:0] instr_cmd,
    input [INSTR_DATA_WIDTH-1:0] instr_data,

    input [DATA_00_WIDTH-1:0] data_0,
    input [DATA_01_WIDTH-1:0] data_1,
    input [DATA_02_WIDTH-1:0] data_2,
    input [DATA_03_WIDTH-1:0] data_3,
    input [DATA_04_WIDTH-1:0] data_4,
    input [DATA_05_WIDTH-1:0] data_5,
    input [DATA_06_WIDTH-1:0] data_6,    
    input [DATA_07_WIDTH-1:0] data_7,
    input [DATA_08_WIDTH-1:0] data_8,
    input [DATA_09_WIDTH-1:0] data_9,
    input [DATA_10_WIDTH-1:0] data_10,
    input [DATA_11_WIDTH-1:0] data_11,
    input [DATA_12_WIDTH-1:0] data_12,
    input [DATA_13_WIDTH-1:0] data_13,
    input [DATA_14_WIDTH-1:0] data_14,
    input [DATA_15_WIDTH-1:0] data_15,
    
    output reg [SCOPE_WIDTH-1:0] scope_tdata,
    output wire scope_tvalid,
    output reg trig,
    output reg [SAMPLES_WIDTH-1:0] samples,
    output reg [DEC_WIDTH-1:0] dec
);

    //instruction commands
    localparam CMD_SRC = 'h0, CMD_ACQ = 'h1, CMD_DEC = 'h2;
    
    reg [3 : 0] src;

    always @(posedge clk) begin
        if(resetn == 0) begin
            src <= 0;
            trig <= 0;
            samples <= 1;
            dec <= 1;
        end else begin
            if((en==1) && (instr_valid == 1)) begin
                case(instr_cmd)
                    CMD_SRC: begin
                        src <= instr_data[3 : 0];
                        trig <= 0;
                        samples <= samples;
                        dec <= dec;
                    end
                    CMD_ACQ: begin
                        src <= src;
                        trig <= 1;
                        samples <= instr_data[SAMPLES_WIDTH - 1 : 0];
                        dec <= dec;
                    end
                    
                    CMD_DEC: begin
                        src <= src;
                        trig <= 0;
                        samples <= samples;
                        dec <= instr_data[DEC_WIDTH - 1 : 0];
                    end
                    default: begin
                        src <= src;
                        trig <= 0;
                        samples <= samples;
                        dec <= dec;
                    end
                endcase

            end else begin
                src <= src;
                trig <= 0;
                samples <= samples;
                dec <= dec;
            end
        end
    end

    
    assign scope_tvalid = 1;
    always @(posedge clk) begin
        if(resetn == 0) begin
            scope_tdata <= 0;
        end
        else begin
            case(src) 
                0: scope_tdata <= data_0;
                1: scope_tdata <= data_1;
                2: scope_tdata <= data_2;
                3: scope_tdata <= data_3;
                4: scope_tdata <= data_4;
                5: scope_tdata <= data_5;
                6: scope_tdata <= data_6;
                7: scope_tdata <= data_7;
                8: scope_tdata <= data_8;
                9: scope_tdata <= data_9;
                10: scope_tdata <= data_10;
                11: scope_tdata <= data_11;
                12: scope_tdata <= data_12;
                13: scope_tdata <= data_13;
                14: scope_tdata <= data_14;
                15: scope_tdata <= data_15;
                default: scope_tdata <= 0;
            endcase
        end
    end
    
    

endmodule