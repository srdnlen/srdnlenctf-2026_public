# Cornflake v3.5

**Category:** rev\
**Difficulty:** medium\
**Authors:** @Salsa

## Description

The evolution of a Cereal Offender

## **Overview**

The challenge consists of a multi-stage execution flow designed to mimic actual malware:

1. **Stage 1 (malware.exe)**: A Windows loader that performs an environment check (username), downloads a second stage from a C2, and manually maps it into memory.  
2. **Stage 2 (payload.dll)**: A manually mapped DLL that implements a custom Virtual Machine (VM) to validate the flag stored in password.txt.

## **Stage 1: Loader Analysis**

The loader malware.exe first checks if the current user is the intended target. It uses GetUserNameA and encrypts the result using **RC4**.

### **RC4 Check**

* **Key**: s3cr3t\_k3y\_v1  
* **Target Hex**: 46f5289437bc009c17817e997ae82bfbd065545d

By decrypting the hex string with the key, we find the required username: super\_powerful\_admin.

### **Payload Delivery**

Once the check passes, the loader connects to cornflake.challs.srdnlen.it:8000/updates/check.php?SessionID=... to download the payload. Instead of using standard Windows loading functions, it uses **Manual Mapping** (this is not relevant to solve the challenge)

## **Stage 2: VM Analysis**

The core of the challenge is in the payload.dll. It reads a flag from password.txt and runs it through a stack-based VM.

### **VM Architecture**

The VM uses three registers (eax, ebx, ecx) and a stack.

| Opcode | Mnemonic | Description |
| :---- | :---- | :---- |
| 1 | PUSH | Pushes ecx to stack. |
| 2 | MOD\_NEXT | Self-modifies: bytecode\[i+1\] \+= eax. This is used to "skip" failure opcodes. |
| 3 | POP | Pops to ebx. |
| 4 | CMP | eax \= (ebx \== ecx). |
| 5 | FALSE | Immediate failure (returns \-1). |
| 7 | XOR | eax ^= ebx. |
| 12 | LOAD\_PREV | eax \= bytecode\[i-1\]. Used for loading constants. |
| 13 | READ\_ABS | ebx \= password\[eax\]. |

### **The "Skip" Logic**

The VM's security depends on a self-modifying trick. A typical check looks like this:  
\# Pseudo-bytecode  
READ\_CHAR(0)  \# eax \= flag\[0\]  
CMP 's'       \# eax \= 1 if match  
MOD\_NEXT      \# If eax is 1, the next byte (FALSE) becomes 5+1 \= 6 (TRUE/NOP)  
FALSE         \# If we didn't match, we hit 5 and exit.

## **Solving the Constraints**

The bytecode implements several mathematical checks on the flag characters. By analyzing the VM instructions, we can extract the following logic:

1. **Simple Checks**: flag\[0\] \== 's', flag\[3\] \== 'n', etc.  
2. **Arithmetic Templates**:  
   * **Mix**: (flag\[idx1\] \+ 3\) ^ (flag\[idx2\] \- 2\) \== value  
   * **Sub Mix**: (flag\[idx1\] \- flag\[idx2\]) ^ flag\[idx3\] \== value  
   * **Div Mix**: ((flag\[idx1\] // 4\) ^ flag\[idx2\]) \+ flag\[idx3\] \== value  
3. **Indirect Indexing**: flag\[1\] is validated by reading flag\[22\], subtracting 48, and using that as an index.  
4. **Batch Sums**: Sums of multiple characters (e.g., flag\[30\] \+ flag\[31\] \+ flag\[32\]).


## **Flag**

After solving the system of equations implemented in the VM (sorry if there were multiple valid flags):  
**`srdnlen{r3v_c4N_l0ok_l1K3_mAlw4r3}`**