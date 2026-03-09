`timescale 1ns / 1ps

module multiplexer(
    input wire CLK,
    input wire RST,
    input wire [4:0] COST_1,
    input wire [4:0] COST_2,
    input wire [4:0] COST_3,
    input wire [4:0] COST_4,
    input wire [4:0] COST_5,
    input wire [4:0] COST_6,
    input wire [4:0] COST_7,
    input wire [4:0] COST_8,
    input wire RESULT_1,
    input wire RESULT_2,
    input wire RESULT_3,
    input wire RESULT_4,
    input wire RESULT_5,
    input wire RESULT_6,
    input wire RESULT_7,
    input wire RESULT_8,
    input wire [2:0] SELECT,
    output reg [4:0] COST,
    output reg RESULT
);
    always @(posedge CLK or posedge RST) begin
        if (RST) begin
            COST = 5'd0;
            RESULT = 1'b0;
        end else begin
            case(SELECT)
                3'd1: begin COST <= COST_1; RESULT <= RESULT_1; end
                3'd2: begin COST <= COST_2; RESULT <= RESULT_2; end
                3'd3: begin COST <= COST_3; RESULT <= RESULT_3; end
                3'd4: begin COST <= COST_4; RESULT <= RESULT_4; end
                3'd5: begin COST <= COST_5; RESULT <= RESULT_5; end
                3'd6: begin COST <= COST_6; RESULT <= RESULT_6; end
                3'd7: begin COST <= COST_7; RESULT <= RESULT_7; end
                default: begin COST <= 5'd0; RESULT <= 1'b0; end
            endcase
        end
    end

endmodule
    
