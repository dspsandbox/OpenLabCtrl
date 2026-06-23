// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module analog #(
    parameter AMPL_DEFAULT = 0,
    parameter PHASE_OFF_DEFAULT = 0,
    parameter PHASE_INCR_DEFAULT = 0,
    localparam AMPL_WIDTH = 16,
    localparam PHASE_WIDTH = 32,
    localparam INSTR_CMD_WIDTH = 4,
    localparam INSTR_DATA_WIDTH = 32,
    parameter AMPL_LATENCY = 8
    
)(
    input clk,
    input resetn,
    input en,
    input instr_valid,
    input [INSTR_CMD_WIDTH-1:0] instr_cmd,
    input [INSTR_DATA_WIDTH-1:0] instr_data,
    output reg [AMPL_WIDTH-1:0] ampl,
    output reg [PHASE_WIDTH-1:0] ph_off,
    output reg [PHASE_WIDTH-1:0] ph_inc,
    output reg ph_rst

);

    reg [AMPL_WIDTH-1:0] ampl_reg;
    reg [PHASE_WIDTH-1:0] ph_off_reg;
    reg [PHASE_WIDTH-1:0] ph_inc_reg;
    reg ph_rst_reg;
    reg update_reg;
    
    
    //instruction commands
    localparam CMD_PH = 'h0, CMD_PH_RST = 'h1, CMD_FREQ = 'h2, CMD_AMPL = 'h3;

    //Update internal registers based on instruction
    always @(posedge clk) begin
        if (resetn == 0) begin
            ph_off_reg <= PHASE_OFF_DEFAULT;
            ph_rst_reg <= 0;
            ph_inc_reg <= PHASE_INCR_DEFAULT;
            ampl_reg <= AMPL_DEFAULT;
            update_reg <= 0;
        end else begin
            if ((en == 1) && (instr_valid == 1)) begin
                case(instr_cmd[INSTR_CMD_WIDTH-2:0])
                    CMD_PH: begin
                        ph_off_reg <= instr_data[PHASE_WIDTH-1:0];
                        ph_rst_reg <= 0;
                        ph_inc_reg <= ph_inc_reg;
                        ampl_reg <= ampl_reg;
                        update_reg <= instr_cmd[INSTR_CMD_WIDTH-1];
                    end
                    CMD_PH_RST: begin
                        ph_off_reg <= ph_off_reg;
                        ph_rst_reg <= instr_data[0];
                        ph_inc_reg <= ph_inc_reg;
                        ampl_reg <= ampl_reg;
                        update_reg <= instr_cmd[INSTR_CMD_WIDTH-1];
                    end
                    CMD_FREQ: begin
                        ph_off_reg <= ph_off_reg;
                        ph_rst_reg <= 0;
                        ph_inc_reg <= instr_data[PHASE_WIDTH-1:0];
                        ampl_reg <= ampl_reg;
                        update_reg <= instr_cmd[INSTR_CMD_WIDTH-1];
                    end
                    CMD_AMPL: begin
                        ph_off_reg <= ph_off_reg;
                        ph_rst_reg <= 0;
                        ph_inc_reg <= ph_inc_reg;
                        ampl_reg <= instr_data[AMPL_WIDTH-1:0];
                        update_reg <= instr_cmd[INSTR_CMD_WIDTH-1];
                    end
                    default: begin
                        ampl_reg <= ampl_reg;
                        ph_off_reg <= ph_off_reg;
                        ph_inc_reg <= ph_inc_reg;
                        ph_rst_reg <= 0;
                        update_reg <= 0;
                    end
                endcase

            end else begin
                ampl_reg <= ampl_reg;
                ph_off_reg <= ph_off_reg;
                ph_inc_reg <= ph_inc_reg;
                ph_rst_reg <= 0;
                update_reg <= 0;
            end
        end
        
    end

    reg [AMPL_WIDTH-1:0] ampl_delay_line [0:AMPL_LATENCY-1];
    integer i;


   

    //Transfer from internal registers to output when UPDATE=1. Additional latency logic for amplitude output
    always @(posedge clk) begin
        if(resetn==0) begin
            ampl <= AMPL_DEFAULT;
            ph_off <= PHASE_OFF_DEFAULT;
            ph_inc <= PHASE_INCR_DEFAULT;
            ph_rst <= 0;

            for (i = 0; i < AMPL_LATENCY; i = i + 1) begin
                ampl_delay_line[i] <= AMPL_DEFAULT;
            end

        end else begin
            if (update_reg == 1) begin
                ampl_delay_line[0] <= ampl_reg;
                ph_off <= ph_off_reg;
                ph_inc <= ph_inc_reg;
                ph_rst <= ph_rst_reg;
            end else begin
                ampl_delay_line[0] <= ampl_delay_line[0];
                ph_off <= ph_off;
                ph_inc <= ph_inc;
                ph_rst <= ph_rst;
            end

            ampl <= ampl_delay_line[AMPL_LATENCY-1];
            for (i = 1; i < AMPL_LATENCY; i = i + 1) begin
                ampl_delay_line[i] <= ampl_delay_line[i-1];
            end

            

        end
    end
endmodule