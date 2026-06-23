// SPDX-License-Identifier: MIT
// Author: Pau Gómez (2026)
// OpenLabCtrl - FPGA-timed experiment control on Red Pitaya STEMlab 125-14

module tb_sync#(
    localparam INSTR_WIDTH = 64,
    localparam INSTR_CMD_LSB = 56,
    localparam INSTR_CMD_MSB = 59,
    localparam INSTR_TIME_LSB = 32,
    localparam INSTR_TIME_MSB = 55,
    localparam INSTR_DATA_LSB = 0,
    localparam INSTR_DATA_MSB = 31,
    localparam SHIFT_REG_WIDTH = 5
) ();
    reg clk;
    reg resetn;
    reg en;
    reg flush_fifo;
    
    reg trig_ext_i;
    
    reg done_i;
    reg sync_daisy_1_i;
    reg sync_daisy_2_i;
    
    wire sync_daisy_1_o;
    wire sync_daisy_2_o;

    reg [INSTR_WIDTH-1:0] S00_AXIS_tdata;
    reg S00_AXIS_tvalid;
    wire S00_AXIS_tready;

    wire [INSTR_TIME_MSB-INSTR_TIME_LSB:0] time_counter;

    wire trig_o;


    sync uut (
        .clk(clk),
        .resetn(resetn),
        .en(en),
        .flush_fifo(flush_fifo),
        .trig_ext_i(trig_ext_i),
        .done_i(done_i),
        .sync_daisy_1_i(sync_daisy_1_i),
        .sync_daisy_2_i(sync_daisy_2_i),
        .sync_daisy_1_o(sync_daisy_1_o),
        .sync_daisy_2_o(sync_daisy_2_o),
        .S00_AXIS_tdata(S00_AXIS_tdata),
        .S00_AXIS_tvalid(S00_AXIS_tvalid),
        .S00_AXIS_tready(S00_AXIS_tready),
        .time_counter(time_counter),
        .trig_o(trig_o)
    );


    //instruction commands
    localparam CMD_TRIG_SRC = 'h0;
    
    //trigger sources
    localparam TrigNone = 0, TrigExtHigh = 1, TrigExtLow = 2, TrigExtRise = 3, TrigExtFall = 4, TrigExtRiseFall = 5, TrigSyncDaisyChain = 6;

    
    always begin
        clk = 0; #5;
        clk = 1; #5;
    end


    initial begin
        resetn <= 0;
        en <= 0;
        flush_fifo <= 0;
        trig_ext_i <= 0;
        done_i <= 0;
        sync_daisy_1_i <= 0;
        sync_daisy_2_i <= 0;
        S00_AXIS_tdata <= 0;
        S00_AXIS_tvalid <= 0;
        #20;

        resetn <= 1;
        #20;

        //test 1: check that trig_o is asserted 1 clk after receiving TrigNone, verify increment of time_counter, verify tready goes high again after done_i is asserted
        
        en <= 1;
        #10;
        S00_AXIS_tdata <= ((CMD_TRIG_SRC << INSTR_CMD_LSB) | (TrigNone << INSTR_DATA_LSB)) ;
        S00_AXIS_tvalid <= 1;
        #10;
        if ((trig_o != 1) || (S00_AXIS_tready != 0)) $display("Test 1A failed: trig_o should be high after receiving TrigNone and tready should be low");
        else $display("Test 1A passed");
        S00_AXIS_tvalid <= 0;
        #50;
        if (time_counter != 4)  $display("Test 1B failed: time_counter should increment while in WAIT_DONE state");
        else $display("Test 1B passed");

        done_i <= 1;
        #10;
        done_i <= 0;
        if (S00_AXIS_tready != 1) $display("Test 1C failed: tready should be high after done_i is asserted");
        else $display("Test 1C passed");     


        //test 2: check that trig_o is asserted when receiving TrigExtHigh and trig_ext_i is high 
        S00_AXIS_tdata <= ((CMD_TRIG_SRC << INSTR_CMD_LSB) | (TrigExtHigh << INSTR_DATA_LSB)) ;
        S00_AXIS_tvalid <= 1;
        #10;
        S00_AXIS_tvalid <= 0;
        trig_ext_i <= 1;
        #(10 * SHIFT_REG_WIDTH);
        if (trig_o != 1) $display("Test 2 failed: trig_o should be high when receiving TrigExtHigh and trig_ext_i is high");
        else $display("Test 2 passed");
        #50;
        done_i <= 1;
        #10;
        done_i <= 0;
        #10;

        //test 3: check that trig_o is asserted when receiving TrigExtLow and trig_ext_i is low
        S00_AXIS_tdata <= ((CMD_TRIG_SRC << INSTR_CMD_LSB) | (TrigExtLow << INSTR_DATA_LSB)) ;
        S00_AXIS_tvalid <= 1;
        #10;
        S00_AXIS_tvalid <= 0;
        trig_ext_i <= 0;
        #(10 * SHIFT_REG_WIDTH);
        if (trig_o != 1) $display("Test 3 failed: trig_o should be high when receiving TrigExtLow and trig_ext_i is low");
        else $display("Test 3 passed");
        #50;
        done_i <= 1;
        #10;
        done_i <= 0;
        #10;

        //test 4: check that trig_o is asserted when receiving TrigExtRise and trig_ext_i has a rising edge
        S00_AXIS_tdata <= ((CMD_TRIG_SRC << INSTR_CMD_LSB) | (TrigExtRise << INSTR_DATA_LSB)) ;
        S00_AXIS_tvalid <= 1;
        #10;
        S00_AXIS_tvalid <= 0;
        trig_ext_i <= 1;
        #(10 * SHIFT_REG_WIDTH);
        if (trig_o != 1) $display("Test 4 failed: trig_o should be high when receiving TrigExtRise and trig_ext_i has a rising edge");
        else $display("Test 4 passed");
        #50;
        done_i <= 1;
        #10;
        done_i <= 0;
        #10;

        //test 5: check that trig_o is asserted when receiving TrigExtFall and trig_ext_i has a falling edge
        S00_AXIS_tdata <= ((CMD_TRIG_SRC << INSTR_CMD_LSB) | (TrigExtFall << INSTR_DATA_LSB)) ;
        S00_AXIS_tvalid <= 1;
        #10;
        S00_AXIS_tvalid <= 0;
        trig_ext_i <= 0;
        #(10 * SHIFT_REG_WIDTH);
        if (trig_o != 1) $display("Test 5 failed: trig_o should be high when receiving TrigExtFall and trig_ext_i has a falling edge");
        else $display("Test 5 passed");
        #50;
        done_i <= 1;
        #10;
        done_i <= 0;
        #10;

        //test 6: check that trig_o is asserted when receiving TrigExtRiseFall and trig_ext_i has a rising edge followed by a falling edge
        S00_AXIS_tdata <= ((CMD_TRIG_SRC << INSTR_CMD_LSB) | (TrigExtRiseFall << INSTR_DATA_LSB)) ;
        S00_AXIS_tvalid <= 1;
        #10;
        S00_AXIS_tvalid <= 0;
        trig_ext_i <= 1;
        #(10 * SHIFT_REG_WIDTH);
        if (trig_o != 1) $display("Test 6A failed: trig_o should be high when receiving TrigExtRiseFall and trig_ext_i has a rising edge followed by a falling edge");
        else $display("Test 6A passed");
        #50;
        done_i <= 1;
        #10;
        done_i <= 0;
        #10;

        S00_AXIS_tvalid <= 1;
        #10;
        S00_AXIS_tvalid <= 0;
        trig_ext_i <= 0;
        #(10 * SHIFT_REG_WIDTH);
        trig_ext_i <= 0;
        if (trig_o != 1) $display("Test 6B failed: trig_o should be high when receiving TrigExtRiseFall and trig_ext_i has a rising edge followed by a falling edge");
        else $display("Test 6B passed");
        #50;
        done_i <= 1;
        #10;
        done_i <= 0;
        #10;

        //test 7: check daisy trig (simultaneous assertion of sync_daisy_1_i, sync_daisy_2_i, and done_i)
        S00_AXIS_tdata <= ((CMD_TRIG_SRC << INSTR_CMD_LSB) | (TrigSyncDaisyChain << INSTR_DATA_LSB)) ;
        S00_AXIS_tvalid <= 1;
        #10;
        S00_AXIS_tvalid <= 0;
        #50
        done_i <= 1;
        #0.01; //combination logic delay
        
        if ((trig_o != 0) || (sync_daisy_1_o != 0) || (sync_daisy_2_o != 0)) $display("Test 7A failed: trig_o, sync_daisy_1_o and sync_daisy_2_o should be low when only done_i is high");
        else $display("Test 7A passed");

        sync_daisy_1_i <= 1;
        #0.01; //combination logic delay

        if ((trig_o != 0) || (sync_daisy_1_o != 0) || (sync_daisy_2_o != 1)) $display("Test 7B failed: sync_daisy_2_o should be high when sync_daisy_1_i and done_i are high, trig_o should be low and sync_daisy_1_o should be low");
        else $display("Test 7B passed");

        sync_daisy_1_i <= 0;
        sync_daisy_2_i <= 1;
        #0.01; //combination logic delay

        if ((trig_o != 0) || (sync_daisy_1_o != 1) || (sync_daisy_2_o != 0)) $display("Test 7C failed: sync_daisy_1_o should be high when sync_daisy_2_i and done_i are high, trig_o should be low and sync_daisy_2_o should be low");
        else $display("Test 7C passed");

        sync_daisy_1_i <= 1;
        sync_daisy_2_i <= 1;
        #0.01; //combination logic delay

        if ((trig_o != 0) || (sync_daisy_1_o != 1) || (sync_daisy_2_o != 1)) $display("Test 7D failed: sync_daisy_1_o and sync_daisy_2_o should be high when sync_daisy_1_i, sync_daisy_2_i and done_i are high, trig_o should be low");
        else $display("Test 7D passed");
        
        #(10 * SHIFT_REG_WIDTH);

        if (trig_o != 1) $display("Test 7E failed: trig_o should be high when sync_daisy_1_i, sync_daisy_2_i and done_i are high");
        else $display("Test 7E passed");

         done_i <= 0;
         #50;


    end

endmodule