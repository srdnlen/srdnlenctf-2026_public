`timescale 1ns / 1ps

module vending_machine(
    input wire CLK,
    input wire RST,
    input wire COIN,
    input wire [2:0] CHOICE,
    input wire CANCEL,
    output wire [4:0] COINS_INSERTED,
    output wire [7:0] PRODUCT_DISPENSED,
    output wire [7:0] ENABLE_DEBUG 
);

    wire [7:0] ENABLE;
    wire CANCEL_TO_MANAGER;
    wire [2:0] SELECT;
    wire [4:0] COST_1, COST_2, COST_3, COST_4, COST_5, COST_6, COST_7, COST_8;
    wire RESULT_1, RESULT_2, RESULT_3, RESULT_4, RESULT_5, RESULT_6, RESULT_7, RESULT_8;
    wire GIVE_1, GIVE_2, GIVE_3, GIVE_4, GIVE_5, GIVE_6, GIVE_7, GIVE_8;
    wire [4:0] COST_SELECTED;
    wire RESULT_SELECTED;
    localparam PRICE_P1 = 5'd3;
    localparam PRICE_P2 = 5'd2;
    localparam PRICE_P3 = 5'd4;
    localparam PRICE_P4 = 5'd5;
    localparam PRICE_P5 = 5'd6;
    localparam PRICE_P6 = 5'd7;
    localparam PRICE_P7 = 5'd3;
    localparam PRICE_P8 = 5'd0;

    money_manager money_mgr(
        .CLK(CLK),
        .RST(RST),
        .COINS(COIN),
        .CANCEL(CANCEL_TO_MANAGER),
        .COST(COST_SELECTED),
        .RESULT(RESULT_SELECTED),
        .COINS_INSERTED(COINS_INSERTED)
    );

    selector sel(
        .CLK(CLK),
        .RST(RST),
        .COINS_INSERTED(COINS_INSERTED),
        .CHOICE(CHOICE),
        .CANCEL_IN(CANCEL),
        .ENABLE(ENABLE),
        .SELECT(SELECT),
        .CANCEL_OUT(CANCEL_TO_MANAGER)
    );

    multiplexer mux(
        .CLK(CLK),
        .RST(RST),
        .COST_1(COST_1),
        .COST_2(COST_2),
        .COST_3(COST_3),
        .COST_4(COST_4),
        .COST_5(COST_5),
        .COST_6(COST_6),
        .COST_7(COST_7),
        .COST_8(COST_8),
        .RESULT_1(RESULT_1),
        .RESULT_2(RESULT_2),
        .RESULT_3(RESULT_3),
        .RESULT_4(RESULT_4),
        .RESULT_5(RESULT_5),
        .RESULT_6(RESULT_6),
        .RESULT_7(RESULT_7),
        .RESULT_8(RESULT_8),
        .SELECT(SELECT),
        .COST(COST_SELECTED),
        .RESULT(RESULT_SELECTED)
    );

    product #(.PRODUCT_ID(1), .PRICE(PRICE_P1)) product_1(
        .CLK(CLK),
        .RST(RST),
        .ENABLE(ENABLE[0]),
        .COINS_INSERTED(COINS_INSERTED),
        .COST(COST_1),
        .RESULT(RESULT_1),
        .GIVE_PRODUCT(GIVE_1)
    );

    product #(.PRODUCT_ID(2), .PRICE(PRICE_P2)) product_2(
        .CLK(CLK),
        .RST(RST),
        .ENABLE(ENABLE[1]),
        .COINS_INSERTED(COINS_INSERTED),
        .COST(COST_2),
        .RESULT(RESULT_2),
        .GIVE_PRODUCT(GIVE_2)
    );

    product #(.PRODUCT_ID(3), .PRICE(PRICE_P3)) product_3(
        .CLK(CLK),
        .RST(RST),
        .ENABLE(ENABLE[2]),
        .COINS_INSERTED(COINS_INSERTED),
        .COST(COST_3),
        .RESULT(RESULT_3),
        .GIVE_PRODUCT(GIVE_3)
    );

    product #(.PRODUCT_ID(4), .PRICE(PRICE_P4)) product_4(
        .CLK(CLK),
        .RST(RST),
        .ENABLE(ENABLE[3]),
        .COINS_INSERTED(COINS_INSERTED),
        .COST(COST_4),
        .RESULT(RESULT_4),
        .GIVE_PRODUCT(GIVE_4)
    );

        product #(.PRODUCT_ID(5), .PRICE(PRICE_P5)) product_5(
        .CLK(CLK),
        .RST(RST),
        .ENABLE(ENABLE[4]),
        .COINS_INSERTED(COINS_INSERTED),
        .COST(COST_5),
        .RESULT(RESULT_5),
        .GIVE_PRODUCT(GIVE_5)
    );

    product #(.PRODUCT_ID(6), .PRICE(PRICE_P6)) product_6(
        .CLK(CLK),
        .RST(RST),
        .ENABLE(ENABLE[5]),
        .COINS_INSERTED(COINS_INSERTED),
        .COST(COST_6),
        .RESULT(RESULT_6),
        .GIVE_PRODUCT(GIVE_6)
    );

    product #(.PRODUCT_ID(7), .PRICE(PRICE_P7)) product_7(
        .CLK(CLK),
        .RST(RST),
        .ENABLE(ENABLE[6]),
        .COINS_INSERTED(COINS_INSERTED),
        .COST(COST_7),
        .RESULT(RESULT_7),
        .GIVE_PRODUCT(GIVE_7)
    );

    product #(.PRODUCT_ID(8), .PRICE(PRICE_P8)) product_8(
        .CLK(CLK),
        .RST(RST),
        .ENABLE(ENABLE[7]),
        .COINS_INSERTED(COINS_INSERTED),
        .COST(COST_8),
        .RESULT(RESULT_8),
        .GIVE_PRODUCT(GIVE_8)
    );

    assign PRODUCT_DISPENSED = {GIVE_8, GIVE_7, GIVE_6, GIVE_5, GIVE_4, GIVE_3, GIVE_2, GIVE_1};
    assign ENABLE_DEBUG = ENABLE;

endmodule






















