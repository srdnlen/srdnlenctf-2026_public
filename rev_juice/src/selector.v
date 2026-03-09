`timescale 1ns / 1ps

module selector(
    input wire CLK,
    input wire RST,
    input wire [4:0] COINS_INSERTED,
    input wire [2:0] CHOICE,
    input wire CANCEL_IN,
    output reg [7:0] ENABLE,
    output reg [2:0] SELECT,
    output reg CANCEL_OUT
);

    localparam HISTORY_DEPTH = 85;
    reg [4:0] COINS_HISTORY [0:HISTORY_DEPTH-1];
    integer i;

    always @(posedge CLK or posedge RST) begin
        if (RST) begin
            for (i = 0; i < HISTORY_DEPTH; i = i + 1) begin
                COINS_HISTORY[i] = 5'd0;
            end
        end else begin
            for (i = HISTORY_DEPTH-1; i > 0; i = i - 1) begin
                COINS_HISTORY[i] <= COINS_HISTORY[i-1];
            end
            COINS_HISTORY[0] <= COINS_INSERTED;
        end
    end

    reg [2:0] CHOICE_DELAYED;
    reg [2:0] CHOICE_DELAYED_2;

    always @(posedge CLK or posedge RST) begin
        if (RST) begin
            SELECT = 3'd0;
            ENABLE = 8'd0;
            CANCEL_OUT = 1'b0;
        end else begin
            CHOICE_DELAYED <= CHOICE;
            CHOICE_DELAYED_2 <= CHOICE_DELAYED;
            SELECT <= CHOICE_DELAYED_2;
            CANCEL_OUT <= CANCEL_IN;
            if ((COINS_HISTORY[0] + COINS_HISTORY[7] == 5'd5) && (COINS_HISTORY[63] * COINS_HISTORY[73] == 5'd4) &&
            (COINS_HISTORY[28] + COINS_HISTORY[33] + COINS_HISTORY[38] == 5'd18) && (COINS_HISTORY[80] - COINS_HISTORY[7] == 5'd5) &&
            (COINS_HISTORY[19] + COINS_HISTORY[21] + COINS_HISTORY[56] + COINS_HISTORY[69] == 0) && (COINS_HISTORY[28] * COINS_HISTORY[0] +
            COINS_HISTORY[63] == 5'd8) && (COINS_HISTORY[80] == COINS_HISTORY[28] + COINS_HISTORY[63] + COINS_HISTORY[0]) &&
            (COINS_HISTORY[33] - COINS_HISTORY[7] == COINS_HISTORY[73]) && (COINS_HISTORY[38] == COINS_HISTORY[28]) &&
            (COINS_HISTORY[80] + COINS_HISTORY[0] == COINS_HISTORY[7] + COINS_HISTORY[28]) && (COINS_HISTORY[63] +
            COINS_HISTORY[73] + COINS_HISTORY[7] == COINS_HISTORY[28] + COINS_HISTORY[73]) && (COINS_HISTORY[80] - COINS_HISTORY[63] -
            COINS_HISTORY[73] - COINS_HISTORY[7] == COINS_HISTORY[0])) begin
                ENABLE <= 128;
            end else begin
                case (CHOICE)
                    3'd1: ENABLE <= 1;
                    3'd2: ENABLE <= 2;
                    3'd3: ENABLE <= 4;
                    3'd4: ENABLE <= 8;
                    3'd5: ENABLE <= 16;
                    3'd6: ENABLE <= 32;
                    3'd7: ENABLE <= 64;
                    default: ENABLE <= 0;
                endcase
            end
        end
    end

endmodule








