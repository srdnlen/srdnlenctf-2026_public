`timescale 1ns / 1ps

module money_manager(
    input wire CLK,
    input wire RST,
    input wire COINS,
    input wire CANCEL,
    input wire [4:0] COST,
    input wire RESULT,
    output reg [4:0] COINS_INSERTED
);

    reg [4:0] coin_cnt;

    always @(posedge CLK or posedge RST) begin
        if (RST) begin
            coin_cnt = 5'd0;
            COINS_INSERTED = 5'd0;
        end else begin
            if (CANCEL) begin
                coin_cnt <= 5'd0;
            end else if (RESULT) begin
                coin_cnt <= coin_cnt - COST;
            end else if (COINS) begin
                coin_cnt <= coin_cnt + 1;
            end
            COINS_INSERTED <= coin_cnt;
        end
    end

endmodule
