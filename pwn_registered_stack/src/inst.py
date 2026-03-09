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

        
