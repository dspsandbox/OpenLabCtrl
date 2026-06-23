// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module tb_instr_breakout#(
    localparam INSTR_WIDTH = 64,
    localparam INSTR_CMD_LSB = 56,
    localparam INSTR_CMD_MSB = 59,
    localparam INSTR_TIME_LSB = 32,
    localparam INSTR_TIME_MSB = 55,
    localparam INSTR_DATA_LSB = 0,
    localparam INSTR_DATA_MSB = 31
) ();
    reg clk;
    reg resetn;
    reg en;
    reg flush_fifo;
    reg trig;
    
    reg [INSTR_TIME_MSB-INSTR_TIME_LSB:0] time_counter;

    reg [INSTR_WIDTH-1:0] S00_AXIS_tdata;
    reg S00_AXIS_tvalid;
    wire S00_AXIS_tready;

    wire error;
    
    wire done;
    wire instr_valid;
    wire [INSTR_CMD_MSB-INSTR_CMD_LSB:0] instr_cmd;
    wire [INSTR_DATA_MSB-INSTR_DATA_LSB:0] instr_data;

    //instruction format
    localparam CMD_DONE = 'hE, CMD_NOP = 'hF;
    
    //fsm states
    localparam IDLE = 0, RUNNING = 1, ERROR = 2;

    instr_breakout uut (
        .clk(clk),
        .resetn(resetn),
        .en(en),
        .flush_fifo(flush_fifo),
        .trig(trig),
        .time_counter(time_counter),
        .S00_AXIS_tdata(S00_AXIS_tdata),
        .S00_AXIS_tvalid(S00_AXIS_tvalid),
        .S00_AXIS_tready(S00_AXIS_tready),
        .error(error),
        .done(done),
        .instr_valid(instr_valid),
        .instr_cmd(instr_cmd),
        .instr_data(instr_data)
    );
    


    
    always begin
        clk = 0; #5;
        clk = 1; #5;
    end

    initial begin
        resetn <= 0;
        en <= 0;
        flush_fifo <= 0;
        trig <= 0;
        time_counter <= 0;
        S00_AXIS_tdata <= 0;
        S00_AXIS_tvalid <= 0;
        #10;
        resetn <= 1;
        #20;

        //test 1: check that error goes high when tvalid is low while waiting for instruction
        en <= 1;
        trig <= 1;
        #20;
        if (error != 1) $display("Test 1A failed: error should be high when tvalid is low while waiting for instruction");
        else $display("Test 1A passed");

        //test 1B: check that error goes if en goes low
        en <= 0;
        trig <= 0;
        #20;
        if (error == 1) $display("Test 1B failed: error should return low when en goes low");
        else $display("Test 1B passed");

        //test 2: check that instructions are processed when time_counter and time_i coincide
        en <= 1;
        trig <= 1;
        S00_AXIS_tdata <= {8'h0, 24'h5, 32'h12345678}; //NOP at time 0
        S00_AXIS_tvalid <= 1;
        #10;
        if ((instr_valid == 1) && (S00_AXIS_tready == 1)) $display("Test 2A failed: instr_valid and tready should be high when time_i and time_counter coincide");
        else $display("Test 2A passed");
        time_counter <= 5;
        trig <= 0;
        #10;
        if ((instr_valid == 0) || (S00_AXIS_tready == 0)) $display("Test 2B failed: instr_valid and tready should be high when time_i and time_counter coincide");
        else $display("Test 2B passed");
        #10;

        //test 3: check that flush_fifo enables tready regardless of time_i and time_counter
        flush_fifo <= 1;
        #10;
        if (S00_AXIS_tready != 1) $display("Test 3 failed: tready should be high when flush_fifo is high regardless of time_i and time_counter");
        else $display("Test 3 passed");
        
        //test 4: check that instruction is not processed when CMD_NOP is sent
        flush_fifo <= 0;
        S00_AXIS_tdata <= {8'hf, 24'h0, 32'h12345678}; //NOP at time 0
        S00_AXIS_tvalid <= 1;
        time_counter <= 0;
        #10;
        if ((instr_valid == 1) || (S00_AXIS_tready == 0)) $display("Test 4 failed: instr_valid should be low and tready should be high when CMD_NOP is sent");
        else $display("Test 4 passed");
        

        //test 5: check that done goes high when CMD_DONE is sent
        S00_AXIS_tdata <= {8'he, 24'h0, 32'h12345678}; //DONE at time 0
        S00_AXIS_tvalid <= 1;
        time_counter <= 0;
        #10;
        if (done != 1) $display("Test 5 failed: done should be high when CMD_DONE is sent");
        else $display("Test 5 passed");

        //test 6: check that done goes low when triggered again after CMD_DONE
        trig <= 1;
        S00_AXIS_tdata <= 0;
        S00_AXIS_tvalid <= 1;
        time_counter <= 0;
        #10;
        trig <= 0;
        if (done != 0) $display("Test 6 failed: done should be low when triggered again after CMD_DONE");
        else $display("Test 6 passed");

        //test 7: check that 

        $finish;

    end





    




        
endmodule