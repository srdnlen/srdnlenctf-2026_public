`timescale 1ns / 1ps

module product #(
    parameter PRODUCT_ID = 1,
    parameter PRICE = 5'd3
)(
    input wire CLK,
    input wire RST,
    input wire ENABLE,
    input wire [4:0] COINS_INSERTED,
    output reg RESULT,
    output reg [4:0] COST,
    output reg GIVE_PRODUCT
);

    reg ENABLE_DELAYED;

    always @(posedge CLK or posedge RST) begin
        if (RST) begin
            GIVE_PRODUCT = 0;
            COST = 5'd0;
            RESULT = 0;
            ENABLE_DELAYED = 0;
        end else begin
            ENABLE_DELAYED <= ENABLE;
            if (ENABLE_DELAYED) begin
                COST <= PRICE;
                RESULT <= (COINS_INSERTED >= PRICE) ? 1'b1 : 1'b0;
                GIVE_PRODUCT <= (COINS_INSERTED >= PRICE) ? 1'b1 : 1'b0;
            end else begin
                COST <= 5'd0;
                RESULT <= 1'b0;
                GIVE_PRODUCT <= 1'b0;
            end
        end
    end

endmodule


    
