// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module stream_ctrl #(
    parameter DATA_WIDTH = 16,
    localparam SAMPLES_WIDTH = 32
)(
    input clk,
    input resetn,
    input err_i, 
    output err_o,
    input en,
    input [SAMPLES_WIDTH-1:0] samples_total,
    input trig, 
    input [SAMPLES_WIDTH-1:0] samples,
    input [SAMPLES_WIDTH-1:0] dec,
    input [DATA_WIDTH - 1 : 0] stream_i_tdata,
    input stream_i_tvalid,
    output stream_i_tready,
    output [DATA_WIDTH - 1 : 0] stream_o_tdata,
    output stream_o_tvalid,
    output stream_o_tlast,
    input stream_o_tready
);
    
    localparam IDLE=0, RUNNING=1, ERROR=2;
    reg [0 : 1] state;
    reg [SAMPLES_WIDTH-1 : 0] counter_samples;
    reg [SAMPLES_WIDTH-1 : 0] counter_samples_total;
    reg [SAMPLES_WIDTH-1 : 0] counter_dec;
    
    wire input_ok;
    wire output_ok;
    wire dec_ok;
    wire last_sample;
    wire last_sample_total;
    wire samples_total_ok;

    assign input_ok = stream_i_tvalid;
    assign dec_ok = (counter_dec == 1) ? 1 : 0;
    assign output_ok = stream_o_tready;
    assign last_sample = (counter_samples == samples) ? 1 : 0;
    assign last_sample_total = (counter_samples_total == samples_total) ? 1 : 0;
    assign samples_total_ok = (counter_samples_total <= samples_total) ? 1 : 0;


    //State machine for stream control
    always @(posedge clk) begin
        if ((resetn == 0) || (en == 0)) begin
            state <= IDLE;
        end else begin
            case(state)
                IDLE: begin
                    if(trig == 1) begin
                        state <= RUNNING;
                    end else begin
                        state <= IDLE;
                    end 
                end

                RUNNING: begin                
                    if((trig == 1) || ((input_ok == 1) && (output_ok == 0) && (dec_ok == 1)) || (samples_total_ok == 0)) begin //If a new trigger is received while running, or if the output is not ready when it should be, or if the total number of samples exceeds the configured total, go to error state
                        state <= ERROR;
                    end else begin
                        if((input_ok == 1) && (output_ok == 1) && (dec_ok == 1) && (last_sample == 1)) begin //If the last sample of the acquisition is reached, go back to idle state
                            state <= IDLE;
                        end else begin
                            state <= RUNNING;
                        end
                    end
                end

                ERROR: begin
                    state <= ERROR;  //Stay in error state until reset or disable
                end

                default: begin
                    state <= IDLE;
                end 
            endcase
        end
    end



    //state machine for sample counting
    always @(posedge clk) begin
        if ((resetn == 0) || (en == 0)) begin
            counter_samples <= 1;
            counter_samples_total <= 1;
        end else begin
            case(state)
                IDLE: begin
                    counter_samples <= 1;
                    counter_samples_total <= counter_samples_total;
                end

                RUNNING: begin                
                    if((input_ok == 1) && (output_ok == 1) && (dec_ok == 1)) begin
                        counter_samples <= counter_samples + 1;
                        counter_samples_total <= counter_samples_total + 1;
                    end else begin
                        counter_samples <= counter_samples;
                        counter_samples_total <= counter_samples_total;
                    end
                end

                default: begin
                    counter_samples <= counter_samples;
                    counter_samples_total <= counter_samples_total;
                end 
            endcase
        end
    end


    //state machine for decimation counting
    always @(posedge clk) begin
        if ((resetn == 0) || (en == 0)) begin
            counter_dec <= 1;
        end else begin
            if ((trig == 1) || (counter_dec >= dec)) begin
                counter_dec <= 1;
            end else begin
                counter_dec <= counter_dec + 1;
            end 
        end
    end


    assign stream_o_tdata = stream_i_tdata;
    assign stream_o_tvalid = ((state == RUNNING) && (input_ok == 1) && (dec_ok == 1)) ? 1 : 0;
    assign stream_i_tready = ((state == RUNNING) && (input_ok == 1) && (dec_ok == 1)) ? 1 : 0;
    assign stream_o_tlast = last_sample_total;
    assign err_o = (state == ERROR) || (err_i == 1) ? 1 : 0;

endmodule


