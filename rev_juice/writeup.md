# Rev_Juice

CTF: Srdnlen CTF 2026 Quals

Category: rev/hardware

Difficulty: medium

Authors: @T0mm1 (Tommaso Casti)

## Description
A good rever can help me to get some rev juice???

## Overview
The challenge is composed by five .v files (four modules and a top) and a .txt file for costraints.
It asks us to find a sequence using 19 coins that gives us product 8 respecting the rules of .txt file.

## Solution
In selector.v we can see the conditions to unlock product 8.
They are about the values that the signal COINS_INSERTED assumes over time.

```verilog
            if ((COINS_HISTORY[0] + COINS_HISTORY[7] == 5'd5) && (COINS_HISTORY[63] * COINS_HISTORY[73] == 5'd4) &&
            (COINS_HISTORY[28] + COINS_HISTORY[33] + COINS_HISTORY[38] == 5'd18) && (COINS_HISTORY[80] - COINS_HISTORY[7] == 5'd5) &&
            (COINS_HISTORY[19] + COINS_HISTORY[21] + COINS_HISTORY[56] + COINS_HISTORY[69] == 0) && (COINS_HISTORY[28] * COINS_HISTORY[0] +
            COINS_HISTORY[63] == 5'd8) && (COINS_HISTORY[80] == COINS_HISTORY[28] + COINS_HISTORY[63] + COINS_HISTORY[0]) &&
            (COINS_HISTORY[33] - COINS_HISTORY[7] == COINS_HISTORY[73]) && (COINS_HISTORY[38] == COINS_HISTORY[28]) &&
            (COINS_HISTORY[80] + COINS_HISTORY[0] == COINS_HISTORY[7] + COINS_HISTORY[28]) && (COINS_HISTORY[63] +
            COINS_HISTORY[73] + COINS_HISTORY[7] == COINS_HISTORY[28] + COINS_HISTORY[73]) && (COINS_HISTORY[80] - COINS_HISTORY[63] -
            COINS_HISTORY[73] - COINS_HISTORY[7] == COINS_HISTORY[0])) begin
                ENABLE <= 128;
            end
```

We can solve the system using a python3 script.

```python
from z3 import *

h = [BitVec(f"h{i}", 5) for i in range(12)]

s = Solver()

s.add(h[0] + h[1] == 5)              
s.add(h[8] * h[10] == 4)             
s.add(h[4] + h[5] + h[6] == 18)      
s.add(h[11] - h[1] == 5)             
s.add(h[2] + h[3] + h[7] + h[9] == 0) 
s.add(h[4] * h[0] + h[8] == 8)      
s.add(h[11] == h[4] + h[8] + h[0])   
s.add(h[5] - h[1] == h[10])          
s.add(h[6] == h[4])                  
s.add(h[11] + h[0] == h[1] + h[4])   
s.add(h[8] + h[10] + h[1] == h[4] + h[10]) 
s.add(h[11] - h[8] - h[10] - h[1] == h[0]) 

if s.check() == sat:
    model = s.model()
    result = [model[x].as_long() for x in h]
    print(result)
else:
    print("No solution found")
```

The result is [1, 4, 0, 0, 6, 6, 6, 0, 2, 0, 2, 9].

Now we know which value COINS_INSERTED must have and when but we have to understand how to get them.
To do so it's crucial to understand the vending machine's timing.
The fastest way is to write some verilog testbenches and see how many clock cycles each move needs.
Let's start with the insert of a coin. 
We already know that it takes 3 clock cycles but let's see.

```verilog
// Finding how many clock cycles it takes to inserte a coin

`timescale 1ns / 1ps

module test_1;

    reg CLK;
    reg RST;
    reg COIN;
    wire [4:0] COINS_INSERTED;
    wire [4:0] COINS_HISTORY_0;
    
    assign COINS_HISTORY_0 = dut.sel.COINS_HISTORY[0];
    
    vending_machine dut(
        .CLK(CLK),
        .RST(RST),
        .COIN(COIN),
        .COINS_INSERTED(COINS_INSERTED)
    );
    
    // Frequency = 100MHz, 1 Clock Cycle = 10ns
    initial begin
        CLK = 0;
        forever #5 CLK = ~CLK;
    end
    
    initial begin
        RST = 0;
        COIN = 0;
    
        // Reset high for 2 cycles
        RST = 1;
        #20;
        RST = 0;
        
        // 2 cycles of wait
        #20;
        
        // a coin is inserted
        COIN = 1;
        #10;
        COIN = 0;
        
        // to observe
        #60;
        $finish;
    end
    
endmodule
```
<img width="1622" height="921" alt="Screenshot 2026-03-08 102207" src="https://github.com/user-attachments/assets/984baa8b-c8e8-4028-b47c-6ea0e81a4369" />

As we can see it actually takes 3 clock cycles.
Now let's see the purchase of a product.

```verilog
// Finding how many clock cycles it takes to successfully buy a product

`timescale 1ns / 1ps

module test_2;

    reg CLK;
    reg RST;
    reg COIN;
    reg [2:0] CHOICE;
    wire [2:0] CHOICE_DELAYED;
    wire [2:0] CHOICE_DELAYED_2;
    wire [2:0] SELECT;
    wire ENABLE;
    wire RESULT_4;
    wire [4:0] COST_4;
    wire RESULT;
    wire [4:0] COST;
    wire [4:0] COIN_CNT;
    wire [4:0] COINS_INSERTED;
    wire [4:0] COINS_HISTORY_0;
    
    assign COIN_CNT = dut.money_mgr.coin_cnt;
    assign COINS_HISTORY_0 = dut.sel.COINS_HISTORY[0];
    assign ENABLE = dut.product_4.ENABLE;
    assign COST = dut.mux.COST;
    assign RESULT = dut.mux.RESULT;
    assign SELECT = dut.sel.SELECT;
    assign COST_4 = dut.product_4.COST;
    assign RESULT_4 = dut.product_4.RESULT;
    assign CHOICE_DELAYED = dut.sel.CHOICE_DELAYED;
    assign CHOICE_DELAYED_2 = dut.sel.CHOICE_DELAYED_2;
    
    vending_machine dut(
        .CLK(CLK),
        .RST(RST),
        .COIN(COIN),
        .CHOICE(CHOICE),
        .COINS_INSERTED(COINS_INSERTED)
    );
    
    // Frequency = 100MHz, 1 Clock Cycle = 10ns
    initial begin
        CLK = 0;
        forever #5 CLK = ~CLK;
    end
    
    initial begin
        RST = 0;
        COIN = 0;
        CHOICE = 3'd0;

        // Reset high for 2 cycles
        RST = 1;
        #20;
        RST = 0;
        
        // 2 cycles of wait
        #20;
        
        // 1 coin
        COIN = 1;
        #10;
        COIN = 0;
        #20;
        
        // 2 coin
        COIN = 1;
        #10;
        COIN = 0;
        #20;
        
        // 3 coin
        COIN = 1;
        #10;
        COIN = 0;
        #20;
        
        // 4 coin
        COIN = 1;
        #10;
        COIN = 0;
        #20;
        
        // 5 coin
        COIN = 1;
        #10;
        COIN = 0;
        #20;
        
        // 6 coin
        COIN = 1;
        #10;
        COIN = 0;
        #20;
        
        // select product 4
        CHOICE = 4;
        #10;
        CHOICE = 0;
        
        // to observe
        #80;
        $finish;
    end
    
endmodule
```
<img width="1619" height="881" alt="Screenshot 2026-03-08 102845" src="https://github.com/user-attachments/assets/a8cb2831-fe2b-4307-a6d7-df48cd53ab6f" />

We can see it takes 7 clock cycles (from 225ns to 295ns).
If a product can't be bought because there aren't enough coins the operation will take 2 clock cycles less because COINS_INSERTED and COINS_HISTORY won't be changed.
The last operation we have to check is cancel.

```verilog
// Finding how many clock cycles it takes to cancel if there are coins

`timescale 1ns / 1ps

module test_3;

    reg CLK;
    reg RST;
    reg COIN;
    reg CANCEL;
    wire CANCEL_OUT;
    wire [4:0] COIN_CNT;
    wire [4:0] COINS_INSERTED;
    wire [4:0] COINS_HISTORY_0;
    
    assign COIN_CNT = dut.money_mgr.coin_cnt;
    assign COINS_HISTORY_0 = dut.sel.COINS_HISTORY[0];
    assign CANCEL_OUT = dut.sel.CANCEL_OUT;

    vending_machine dut(
        .CLK(CLK),
        .RST(RST),
        .COIN(COIN),
        .CANCEL(CANCEL),
        .COINS_INSERTED(COINS_INSERTED)
    );
    
    // Frequency = 100MHz, 1 Clock Cycle = 10ns
    initial begin
        CLK = 0;
        forever #5 CLK = ~CLK;
    end
    
    initial begin
        RST = 0;
        COIN = 0;
        CANCEL = 0;

        // Reset high for 2 cycles
        RST = 1;
        #20;
        RST = 0;

        // 1 coin
        COIN = 1;
        #10;
        COIN = 0;
        #20;

        // 2 coins
        COIN = 1;
        #10;
        COIN = 0;
        #20;
        
        // 2 cycles of wait
        #20;
        
        // cancel
        CANCEL = 1;
        #10;
        CANCEL = 0;
        
        // to observe
        #50;
        $finish;
    end
    
endmodule
```
<img width="1615" height="872" alt="Screenshot 2026-03-08 104118" src="https://github.com/user-attachments/assets/37a4a2b6-b3ae-4267-8ff7-ab4fd35ca72e" />

We can see it takes 4 clock cycles (from 105ns to 145ns).
If there aren't coins COINS_INSERTED and COINS_HISTORY won't change so if we do cancel in this case it will take only 2 clock cycles.

Now we know the timing of all operatons:

- Insert n coins = 3*n
  
- Successful purchase of a product = 7
  
- Failed purchase of a product = 5
  
- Cancel when there are coins inserted = 4
  
- Cancel when there are no coins inserted = 2

There may be situations where we can choose between buy and cancel so there are many possibilities.
The idea is to buy every time it is possible, this way we find the max coins number we can use to get product 8 without waste.
A coin spent isn't reusable, a coin "canceled" is given back so we can use it again.
If this number is bigger than 19 we have to try to change some Select with Cancel (where it seems reasonable) to recycle some coins.
If this number is 19 we have pretty much solved the challenge.
If this number is less than 19 we have to waste some coins and there may be more ways to do that.
Let's try to buy everytime it's possible and see what happens.
I will write each step as <value> --[clock cycles]--> <next_value> to explain each choice.

? --[?]--> 9

We don't know what happend before, we can do as many insert and cancel as we like before this point but it's pretty useless.
At the end we will have to insert 9 coins so the first instruction is I9C.

9 --[7]--> 2

This a forced move, the only way to go from 9 to 2 coins in only 7 clock cycles is to buy a product that costs 7 coins.
The move is SP6.

2 --[4]--> 0

Another forced move, the only way to go from 2 to 0 coins in only 4 clock cycles is to cancel.
The move is CNL.

0 --[6]--> 2 --[7]--> 0

These are togheter because they are related. To satisfy the first one we must insert n coins with n >= 2.
To satisfy the second step we need to make COINS_INSERTED return to 0 and this can be done in two ways: buy or cancel.
If we wanna buy (and we do) the moves are I2C and SP2.
If we wanna cancel the moves are I3C and CNL.
It's important to notice how if we go with I2C SP2 we needs (until now) 9 coins and we spend all of them.
If we go with I3C CNL we needs 10 coins but we spend only 7 so we have 3 coins that we can reuse in the next steps.
Taking notes of the coins needed is crucial if we get a number bigger than 19 with se sequence "buy when possible".

0 --[18]--> 6 --[5]--> 6 --[5]--> 6

These are forced moves, the only way to get these values is I6C, SP6 and SP6.

6 --[7]--> 0

We have two options here: SP5 and I1C CNL. As said before we will go with SP5.
Until now we needed 15 coins and spent all of them.

0 --[2]--> 0

Forced move, the only way is using CNL.

0 --[12]--> 4 --[7]--> 1

To satisfy the first step we must insert n coins with n >= 4.
We can easily see that I4C is a forced move because there's no way to go to 1 coin if we insert more than 4 coins so the move is I4C.
The last step can be done in three differente ways:
If we wanna buy a product that costs 3 we have product 1(SP1) and product 7(SP7).
Since is the last step we can also ignore the rule of "buy when possible" and to a cancel followed buy inserting a coin CNL I1C.
At the end if we choose to buy we used 19 coins and spent 18 coins. If we choose cancel + insert we used 19 coins and spent 15 coins.
Since the number we got is exactly 19 we can consider the challenge solved and we have three valid flags.

There may be other sequence to get the product 8 that I missed.
However, if they exists they should necessary use more cancel than I do and then they needs less than 19 coins to work.
For example, if we use the alternative moves I mentioned we only need 14 coins to get product 8.
Is the min number of coins needed to get product 8? I don't know, maybe.
Still, it isn't a valid solution.

The flags are:

*srdnlen{I9C_SP6_CNL_I2C_SP2_I6C_SP6_SP6_SP5_CNL_I4C_SP1}*

*srdnlen{I9C_SP6_CNL_I2C_SP2_I6C_SP6_SP6_SP5_CNL_I4C_SP7}*

*srdnlen{I9C_SP6_CNL_I2C_SP2_I6C_SP6_SP6_SP5_CNL_I4C_CNL_I1C}*
