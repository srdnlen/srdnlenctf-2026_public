import sys

# --- VM Opcode Definitions ---
PUSH        = 1
MOD_NEXT    = 2
POP         = 3
CMP         = 4
FALSE       = 5
TRUE        = 6
XOR         = 7
ADD         = 8
SUB         = 9
READ_REL_N  = 10
READ_REL_P  = 11
LOAD_PREV   = 12
READ_ABS    = 13
MOV_EAX_EBX = 14
MOV_ECX_EAX = 15
MOV_EBX_ECX = 16
MUL         = 17
DIV         = 18

# --- Configuration ---
FLAG = "srdnlen{r3v_c4N_l0ok_l1K3_mAlw4r3}"
bytecode = []

def emit(byte):
    bytecode.append(byte & 0xFF)

# --- Register Movement Helpers ---

def mov_ebx_to_eax():
    emit(MOV_EAX_EBX)

def mov_eax_to_ecx():
    emit(MOV_ECX_EAX)

def mov_ecx_to_ebx():
    emit(MOV_EBX_ECX)

def mov_ebx_to_ecx():
    emit(MOV_EAX_EBX)
    emit(MOV_ECX_EAX)

def mov_eax_to_ebx():
    emit(MOV_ECX_EAX)
    emit(MOV_EBX_ECX)

def mov_ecx_to_eax():
    emit(MOV_EBX_ECX)
    emit(MOV_EAX_EBX)

# --- Value Loading & Assertions ---

def load_imm(val):
    val = val & 0xFF
    if val > 18: 
        emit(val); emit(LOAD_PREV) 
    else:
        # Uses EBX/ECX as scratch!
        mask = 85 
        masked_val = (val ^ mask) & 0xFF
        emit(mask); emit(LOAD_PREV) # eax = 85
        mov_eax_to_ebx()            # ebx = 85
        emit(masked_val); emit(LOAD_PREV) # eax = masked
        emit(XOR)

def assert_eax_match(expected_val):
    expected_val = expected_val & 0xFF
    mov_eax_to_ecx(); emit(PUSH) # Stack: [Result]
    load_imm(expected_val)       # EAX = Expected
    mov_eax_to_ecx()             # ECX = Expected
    emit(POP)                    # EBX = Result
    emit(CMP)                    # EAX = (Result == Expected)
    emit(MOD_NEXT); emit(FALSE)

def read_char_to_eax(index):
    load_imm(index)
    emit(READ_ABS)
    mov_ebx_to_eax()

# --- REUSABLE LOGIC TEMPLATES ---

def template_arithmetic_mix(idx1, idx2):
    """Pattern: (c[idx1] + 3) ^ (c[idx2] - 2)"""
    print(f"[+] Template Arith Mix: Indices {idx1}, {idx2}")
    
    # Part A: c[idx1] + 3
    read_char_to_eax(idx1)
    mov_eax_to_ecx(); emit(PUSH) # Stack: [c1]
    
    load_imm(3); mov_eax_to_ecx()
    emit(POP); emit(ADD) # EBX = c[idx1] + 3
    mov_ebx_to_eax(); mov_eax_to_ecx(); emit(PUSH) # Stack: [ResA]
    
    # Part B: c[idx2] - 2
    load_imm(2); mov_eax_to_ecx(); emit(PUSH) # Stack: [ResA, 2]
    read_char_to_eax(idx2); mov_eax_to_ecx()
    emit(POP); mov_ebx_to_eax()
    emit(SUB) # ECX = c[idx2] - 2
    mov_ecx_to_ebx() # EBX = ResB
    
    # Combine
    mov_ebx_to_eax() # EAX = ResB
    emit(POP); emit(XOR) # EAX = ResB ^ ResA
    
    expected = (ord(FLAG[idx1]) + 3) ^ (ord(FLAG[idx2]) - 2)
    assert_eax_match(expected)

def template_complex_sub(idx1, idx2, idx3):
    """Pattern: (c[idx1] - c[idx2]) ^ c[idx3]"""
    print(f"[+] Template Sub Mix: ({idx1} - {idx2}) ^ {idx3}")
    
    # 1. Load c[idx2] -> Stack (Move to ECX before Push)
    read_char_to_eax(idx2); mov_eax_to_ecx(); emit(PUSH)
    
    # 2. Load c[idx1] -> ECX
    read_char_to_eax(idx1); mov_eax_to_ecx()
    
    # 3. Pop c[idx2] -> EBX -> EAX
    emit(POP); mov_ebx_to_eax()
    
    # 4. SUB (ecx -= eax)
    emit(SUB)
    
    # 5. XOR c[idx3]
    mov_ecx_to_ebx(); mov_ebx_to_eax(); mov_eax_to_ecx(); emit(PUSH)
    read_char_to_eax(idx3); emit(POP); emit(XOR)
    
    val = (ord(FLAG[idx1]) - ord(FLAG[idx2])) ^ ord(FLAG[idx3])
    assert_eax_match(val)

def template_div_complex(idx1, idx2, idx3):
    """Pattern: ((c[idx1] / 4) ^ c[idx2]) + c[idx3]"""
    print(f"[+] Template Div Mix: (({idx1} / 4) ^ {idx2}) + {idx3}")
    
    # 1. Load 4 -> Stack (Move to ECX before Push)
    load_imm(4); mov_eax_to_ecx(); emit(PUSH)
    
    # 2. Load c[idx1] -> EAX
    read_char_to_eax(idx1)
    
    # 3. Pop 4 -> EBX, DIV
    emit(POP); emit(DIV)
    
    # 4. XOR c[idx2]
    mov_eax_to_ecx(); emit(PUSH)
    read_char_to_eax(idx2); emit(POP); emit(XOR)
    
    # 5. ADD c[idx3]
    mov_eax_to_ecx(); emit(PUSH)
    read_char_to_eax(idx3); mov_eax_to_ecx()
    emit(POP); emit(ADD); mov_ebx_to_eax()
    
    p1 = ord(FLAG[idx1]) // 4
    p2 = p1 ^ ord(FLAG[idx2])
    expected = p2 + ord(FLAG[idx3])
    assert_eax_match(expected)

def check_sum_batch(indices):
    print(f"[+] Check Sum Batch: {indices}")
    read_char_to_eax(indices[0])
    mov_eax_to_ecx(); emit(PUSH) # Stack: [Sum]
    
    expected_sum = ord(FLAG[indices[0]])
    
    for idx in indices[1:]:
        read_char_to_eax(idx); mov_eax_to_ecx()
        emit(POP); emit(ADD)
        mov_ebx_to_ecx(); emit(PUSH)
        expected_sum += ord(FLAG[idx])

    emit(POP); mov_ebx_to_eax()
    assert_eax_match(expected_sum)

# --- STANDARD CHECKS ---

def check_01_simple_eq():
    print("[+] Check 1: c[0] == 's'")
    read_char_to_eax(0); assert_eax_match(ord('s'))

def check_03_equality():
    print("[+] Check 3: c[3] == 'n'")
    read_char_to_eax(3); assert_eax_match(ord('n'))

def check_04_char_sum():
    print("[+] Check 4: c[4] + c[5]")
    read_char_to_eax(4); mov_eax_to_ecx(); emit(PUSH)
    read_char_to_eax(5); mov_eax_to_ecx()
    emit(POP); emit(ADD); mov_ebx_to_eax()
    assert_eax_match(ord(FLAG[4]) + ord(FLAG[5]))

def check_05_dynamic_compare():
    print("[+] Check 5: c[6] == c[3]")
    read_char_to_eax(3); mov_eax_to_ecx(); emit(PUSH)
    read_char_to_eax(6); mov_eax_to_ecx()
    emit(POP); emit(CMP); assert_eax_match(1)

def check_06_mul_check():
    print("[+] Check 6: c[8] * 2")
    read_char_to_eax(8); mov_eax_to_ecx(); emit(PUSH) 
    load_imm(2) 
    emit(POP); emit(MUL)
    assert_eax_match(ord(FLAG[8]) * 2)

def check_09_fake_modulo():
    print("[+] Check 9: c[9] % 5")
    # Term 1: 5 * (c[9] / 5)
    
    # 1. Load c[9] -> Stack
    read_char_to_eax(9); mov_eax_to_ecx(); emit(PUSH)
    
    # 2. Load 5 -> EBX (Need to save it, load_imm clobbers)
    load_imm(5); mov_eax_to_ecx(); emit(PUSH) # Stack: [c9, 5]
    
    # 3. Prepare for DIV (Need EAX=c9, EBX=5)
    emit(POP); mov_ebx_to_eax() # EAX = 5 (Popped from Stack)
    emit(POP)                   # EBX = c9 (Popped from Stack)
    
    # Now EAX=5, EBX=c9. We need to swap them for DIV (EAX / EBX)
    mov_eax_to_ecx() # ECX = 5
    mov_ebx_to_eax() # EAX = c9
    mov_ecx_to_ebx() # EBX = 5
    
    emit(DIV) # EAX = c9 / 5
    
    # 4. Mul by 5
    mov_eax_to_ecx(); emit(PUSH) # Stack: [div_res]
    load_imm(5); emit(POP); emit(MUL) # EAX = 5 * (c9/5)
    
    # Save Term1 to Stack
    mov_eax_to_ecx(); emit(PUSH)
    
    # Term 2: c[9]
    read_char_to_eax(9); mov_eax_to_ecx() 
    
    # Subtract
    emit(POP); mov_ebx_to_eax() 
    emit(SUB); mov_ecx_to_eax() # ECX = c[9] - Term1
    assert_eax_match(ord(FLAG[9]) % 5)

def check_10_indirect_indexing():
    print("[+] Check 10: Indirect Read")
    
    # 1. Load 48 -> Stack
    load_imm(48); mov_eax_to_ecx(); emit(PUSH) # Stack: [48]
    
    # 2. Load c[22] -> ECX
    # read_char_to_eax calls load_imm, but Stack is safe.
    read_char_to_eax(22)
    mov_eax_to_ecx() # ECX = 49 ('1')
    
    # 3. Pop 48 -> EBX -> EAX
    emit(POP)        # EBX = 48
    mov_ebx_to_eax() # EAX = 48 (Does NOT clobber ECX)
    
    # 4. SUB
    emit(SUB) # ECX = 49 - 48 = 1
    
    # 5. Read
    mov_ecx_to_eax()
    emit(READ_ABS)   # EBX = passwd[1] ('r')
    mov_ebx_to_eax() # EAX = 'r'
    
    assert_eax_match(ord(FLAG[1]))


def check_11_overflow_trio():
    print("[+] Check 11")
    # c[25] + 2*c[26] - 3*c[27]
    
    # 1. Term 3 (3*c27) -> Stack
    read_char_to_eax(27); mov_eax_to_ecx(); emit(PUSH)
    load_imm(3); emit(POP); emit(MUL)
    mov_eax_to_ecx(); emit(PUSH) # Stack: [Term3]
    
    # 2. Term 1 (c25) -> Stack
    read_char_to_eax(25); mov_eax_to_ecx(); emit(PUSH) # Stack: [Term3, c25]
    
    # 3. Term 2 (2*c26) -> EAX
    read_char_to_eax(26); mov_eax_to_ecx(); emit(PUSH) # PUSH c26 to save from load_imm
    load_imm(2) 
    emit(POP) # EBX = c26
    emit(MUL) # EAX = 2*c26
    
    # 4. Sum
    mov_eax_to_ecx(); emit(POP); emit(ADD) # EBX = Sum
    
    # 5. Sub
    mov_ebx_to_ecx() # ECX = Sum
    emit(POP) # EBX = Term3
    mov_ebx_to_eax() # EAX = Term3
    emit(SUB) # ECX = Sum - Term3
    mov_ecx_to_eax()
    
    t1, t2, t3 = ord(FLAG[25]), 2*ord(FLAG[26]), 3*ord(FLAG[27])
    assert_eax_match(t1 + t2 - t3)

# --- MAIN ---

def main():
    print(f"Building final scrambled bytecode for: {FLAG}")
    check_01_simple_eq()
    template_arithmetic_mix(1, 2)
    check_03_equality()
    check_04_char_sum()
    template_arithmetic_mix(33, 21)
    check_05_dynamic_compare()
    check_06_mul_check()
    
    # FIX: 12, 23 (Swap) to prevent underflow
    template_complex_sub(12, 23, 18)
    template_div_complex(20, 15, 10)
    template_complex_sub(11, 17, 29)
    template_div_complex(7, 16, 28)
    
    check_sum_batch([13, 14])
    check_09_fake_modulo()
    check_10_indirect_indexing()
    check_sum_batch([22, 24])
    check_11_overflow_trio()
    print(len(bytecode))
    check_sum_batch([30, 31, 32])
    
    print(f"Bytecode generated. Length: {len(bytecode)} bytes.")
    print(bytecode)
    with open("bytecode.bin", "wb") as f:
        f.write(bytearray(bytecode))

if __name__ == "__main__":
    main()
