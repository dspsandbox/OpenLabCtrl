// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module instr_breakout#(
    parameter LATENCY = 0,
    localparam INSTR_WIDTH = 64,
    localparam INSTR_CMD_LSB = 56,
    localparam INSTR_CMD_MSB = 59,
    localparam INSTR_TIME_LSB = 32,
    localparam INSTR_TIME_MSB = 55,
    localparam INSTR_DATA_LSB = 0,
    localparam INSTR_DATA_MSB = 31
) (
    input clk,
    input resetn,
    input en,
    input flush_fifo,
    input trig,
    
    input [INSTR_TIME_MSB-INSTR_TIME_LSB:0] time_counter,

    input [INSTR_WIDTH-1:0] S00_AXIS_tdata,
    input S00_AXIS_tvalid,
    output S00_AXIS_tready,

    output error,
    
    output done,
    output reg instr_valid,
    output reg [INSTR_CMD_MSB-INSTR_CMD_LSB:0] instr_cmd,
    output reg [INSTR_DATA_MSB-INSTR_DATA_LSB:0] instr_data
);
    //instruction format
    localparam CMD_DONE = 'hE, CMD_NOP = 'hF;
    
    //fsm states
    localparam IDLE = 0, RUNNING = 1, ERROR = 2;
    reg [1:0] state;

    //extract fields from instruction
    wire [INSTR_CMD_MSB-INSTR_CMD_LSB:0] cmd_i;
    wire [INSTR_TIME_MSB-INSTR_TIME_LSB:0] time_i;
    wire [INSTR_DATA_MSB-INSTR_DATA_LSB:0] data_i;
    assign cmd_i = S00_AXIS_tdata[INSTR_CMD_MSB:INSTR_CMD_LSB];
    assign time_i = S00_AXIS_tdata[INSTR_TIME_MSB:INSTR_TIME_LSB];
    assign data_i = S00_AXIS_tdata[INSTR_DATA_MSB:INSTR_DATA_LSB];
    
    //output signals
    assign done = (en == 1) && (state == IDLE);
    assign error = (en == 1) && (state == ERROR);
    assign S00_AXIS_tready = ((en == 1) && (state == RUNNING) && ((time_i + LATENCY) == time_counter)) || (flush_fifo == 1);


    always @(posedge clk) begin
        if(resetn==0) begin
            state <= IDLE;
            instr_valid <= 0;
            instr_cmd <= 0;
            instr_data <= 0;
        end else begin
            case(state)
                IDLE: begin
                    instr_valid <= 0;
                    if((en == 1) && (trig==1)) begin
                        state <= RUNNING; 
                    end else begin
                        state <= IDLE;
                    end
                end

                RUNNING: begin
                    if (en == 0) begin
                        state <= IDLE;
                        instr_valid <= 0;
                    end else begin 
                        if ((S00_AXIS_tvalid == 0)) begin
                            instr_valid <= 0;
                            state <= ERROR;
                        end else begin
                            if((S00_AXIS_tready == 1) && (S00_AXIS_tvalid == 1))  begin
                                case(cmd_i)
                                    CMD_DONE: begin
                                        instr_valid <= 0;
                                        state <= IDLE;
                                    end
                                    CMD_NOP: begin
                                        instr_valid <= 0;
                                        state <= RUNNING;

                                    end
                                    default: begin
                                        instr_valid <= 1;
                                        instr_cmd <= cmd_i;
                                        instr_data <= data_i; 
                                        state <= RUNNING;                               
                                    end
                                endcase

                            end else begin
                                state <= RUNNING;
                                instr_valid <= 0;
                
                            end
                        end 

                    end
                    
                end

                default: begin #ERROR
                    instr_valid <= 0;
                    if(en == 0) begin
                        state <= IDLE;
                    end else begin
                        state <= ERROR;
                    end
                end
            endcase
        end
    end

    

        
endmodule