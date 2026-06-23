// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module sync#(
    localparam INSTR_WIDTH = 64,
    localparam INSTR_CMD_LSB = 56,
    localparam INSTR_CMD_MSB = 59,
    localparam INSTR_TIME_LSB = 32,
    localparam INSTR_TIME_MSB = 55,
    localparam INSTR_DATA_LSB = 0,
    localparam INSTR_DATA_MSB = 31,
    localparam SHIFT_REG_WIDTH = 5,
    localparam SYNC_COUNTER_WIDTH = 32

) (
    input clk,
    input resetn,
    input en,
    input flush_fifo,
    
    input trig_ext_i,
    
    input done_i,
    input sync_daisy_1_i,
    input sync_daisy_2_i,
    
    output sync_daisy_1_o,
    output sync_daisy_2_o,

    output trig_o,

    input [INSTR_WIDTH-1:0] S00_AXIS_tdata,
    input S00_AXIS_tvalid,
    output S00_AXIS_tready,

    output reg [INSTR_TIME_MSB-INSTR_TIME_LSB:0] time_counter,
    output reg [SYNC_COUNTER_WIDTH-1:0] sync_counter



);
    //instruction commands
    localparam CMD_TRIG_SRC = 'h0;
    
    //trigger sources
    localparam TrigNone = 0, TrigExtHigh = 1, TrigExtLow = 2, TrigExtRise = 3, TrigExtFall = 4, TrigExtRiseFall = 5, TrigSyncDaisyChain = 6;

    //fsm states
    localparam IDLE = 0, TRIG = 1, WAIT_TRIG_EXT_HIGH = 2, WAIT_TRIG_EXT_LOW = 3, WAIT_TRIG_EXT_RISE = 4, WAIT_TRIG_EXT_FALL = 5, WAIT_TRIG_EXT_RISE_FALL = 6, WAIT_SYNC = 7, WAIT_DONE = 8; 
    reg [3:0] state;
    
    //extract fields from instruction
    wire [INSTR_CMD_MSB-INSTR_CMD_LSB:0] cmd_i;
    wire [INSTR_DATA_MSB-INSTR_DATA_LSB:0] data_i;
    assign cmd_i = S00_AXIS_tdata[INSTR_CMD_MSB:INSTR_CMD_LSB];
    assign data_i = S00_AXIS_tdata[INSTR_DATA_MSB:INSTR_DATA_LSB];
    

    //shift registers
    reg [SHIFT_REG_WIDTH-1:0] sr_trig_ext;
    reg [SHIFT_REG_WIDTH-1:0] sr_done;
    reg [SHIFT_REG_WIDTH-1:0] sr_sync_daisy_1;
    reg [SHIFT_REG_WIDTH-1:0] sr_sync_daisy_2;

    always @(posedge clk) begin
        if(resetn == 0) begin
            sr_trig_ext <= 0;
            sr_done <= 0;
            sr_sync_daisy_1 <= 0;
            sr_sync_daisy_2 <= 0;
        end else begin
            sr_trig_ext <= {sr_trig_ext[SHIFT_REG_WIDTH-2:0], trig_ext_i};
            sr_done <= {sr_done[SHIFT_REG_WIDTH-2:0], done_i};
            sr_sync_daisy_1 <= {sr_sync_daisy_1[SHIFT_REG_WIDTH-2:0], sync_daisy_1_i};
            sr_sync_daisy_2 <= {sr_sync_daisy_2[SHIFT_REG_WIDTH-2:0], sync_daisy_2_i};
        end
    end

    

    //sync outputs for daisy chain
    assign sync_daisy_1_o = (en == 1) && (state == WAIT_SYNC) && (done_i == 1) && (sync_daisy_2_i == 1);
    assign sync_daisy_2_o = (en == 1) && (state == WAIT_SYNC) && (done_i == 1) && (sync_daisy_1_i == 1);
    
    //FSM logic
    always @(posedge clk) begin
        if(resetn == 0) begin
            state <= IDLE;
        end else begin
            case(state)
                IDLE: begin
                    if((en == 1) && (S00_AXIS_tvalid == 1)) begin
                        case(cmd_i)
                            CMD_TRIG_SRC: begin
                                case(data_i)
                                    TrigNone: state <= TRIG;
                                    TrigExtHigh: state <= WAIT_TRIG_EXT_HIGH;
                                    TrigExtLow: state <= WAIT_TRIG_EXT_LOW;
                                    TrigExtRise: state <= WAIT_TRIG_EXT_RISE;
                                    TrigExtFall: state <= WAIT_TRIG_EXT_FALL;
                                    TrigExtRiseFall: state <= WAIT_TRIG_EXT_RISE_FALL;
                                    TrigSyncDaisyChain: state <= WAIT_SYNC;
                                    default: state <= IDLE;
                                endcase
                            end
                            default: begin
                                state <= IDLE;
                            end
                        endcase
                    end
                end

                TRIG: begin
                    state <= WAIT_DONE;
                end
                
                WAIT_TRIG_EXT_HIGH: begin
                    if(en == 0) begin
                        state <= IDLE;
                    end else if(sr_trig_ext[SHIFT_REG_WIDTH-2] == 1) begin
                        state <= TRIG;
                    end else begin
                        state <= WAIT_TRIG_EXT_HIGH;
                    end
                end

                WAIT_TRIG_EXT_LOW: begin
                    if(en == 0) begin
                        state <= IDLE;
                    end else if(sr_trig_ext[SHIFT_REG_WIDTH-2] == 0) begin
                        state <= TRIG;
                    end else begin
                        state <= WAIT_TRIG_EXT_LOW;
                    end
                end

                WAIT_TRIG_EXT_RISE: begin
                    if(en == 0) begin
                        state <= IDLE;
                    end else if((sr_trig_ext[SHIFT_REG_WIDTH-1] == 0) && (sr_trig_ext[SHIFT_REG_WIDTH-2] == 1)) begin
                        state <= TRIG;
                    end else begin
                        state <= WAIT_TRIG_EXT_RISE;
                    end
                end

                WAIT_TRIG_EXT_FALL: begin
                    if(en == 0) begin
                        state <= IDLE;
                    end else if((sr_trig_ext[SHIFT_REG_WIDTH-1] == 1) && (sr_trig_ext[SHIFT_REG_WIDTH-2] == 0)) begin
                        state <= TRIG;
                    end else begin
                        state <= WAIT_TRIG_EXT_FALL;
                    end
                end

                WAIT_TRIG_EXT_RISE_FALL: begin
                    if(en == 0) begin
                        state <= IDLE;
                    end else if(((sr_trig_ext[SHIFT_REG_WIDTH-1] == 0) && (sr_trig_ext[SHIFT_REG_WIDTH-2] == 1)) || ((sr_trig_ext[SHIFT_REG_WIDTH-1] == 1) && (sr_trig_ext[SHIFT_REG_WIDTH-2] == 0))) begin
                        state <= TRIG;
                    end else begin
                        state <= WAIT_TRIG_EXT_RISE_FALL;
                    end
                end

                WAIT_SYNC: begin
                    if(en == 0) begin
                        state <= IDLE;
                    end else if((sr_done[SHIFT_REG_WIDTH-2] == 1) && (sr_sync_daisy_1[SHIFT_REG_WIDTH-2] == 1) && (sr_sync_daisy_2[SHIFT_REG_WIDTH-2] == 1)) begin
                        state <= TRIG;
                    end else begin
                        state <= WAIT_SYNC;
                    end
                end

                WAIT_DONE: begin
                    if(en == 0) begin
                        state <= IDLE;
                    end if(done_i == 1) begin
                        state <= IDLE;
                    end else begin
                        state <= WAIT_DONE;
                    end
                end

                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end
    
    //time counter
    always @(posedge clk) begin
        if((resetn == 0) || (en==0))  begin
            time_counter <= 0;
        end else begin
            if(state == WAIT_DONE) begin
                time_counter <= time_counter + 1;
            end else begin
                time_counter <= 0;
            end
        end
    end

    //sync counter
    always @(posedge clk) begin
        if((resetn == 0) || (en==0))  begin
            sync_counter <= 0;
        end else begin
            if(state == TRIG) begin
                sync_counter <= sync_counter + 1;
            end else begin
                sync_counter <= sync_counter;
            end
        end
    end


    //tready logic
    assign S00_AXIS_tready = (((en == 1) && (state == IDLE)) || (flush_fifo==1));

    //trig_o logic
    assign trig_o = (en == 1) && (state == TRIG);
        
endmodule