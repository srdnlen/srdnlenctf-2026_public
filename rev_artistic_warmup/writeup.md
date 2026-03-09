# Artistic Warmup

**Category:** rev\
**Difficulty:** easy\
**Authors:** @Salsa

## Description

> just an easy warmup

## Overview

The challenge is a **Windows PE32+ (x86-64)** executable, stripped. It takes user input via a GDI-rendered window, compares the result pixel-by-pixel against a stored reference bitmap, and prints either `Valid flag!` or `Invalid flag.` accordingly.

## Solution

### Static Analysis — API Hashing

The binary imports no readable Win32 functions. Instead, it resolves all needed API functions at runtime through a custom **export hash resolver** (`sub_140001510`).

The function walks the PE export table of a given module and computes a hash over each exported function name using a djb2-variant algorithm:


The binary first bootstraps itself by walking the **PEB's loader module list** (`InMemoryOrderModuleList`) to find `kernel32.dll` without any import, resolving `LoadLibraryA` (`0x5fbff0fb`). It then loads `gdi32.dll` and resolves the following functions:

| Hash | Function |
|------|----------|
| `0xa05cbae0` | `CreateCompatibleDC` |
| `0xfff5b73d` | `CreateDIBSection` |
| `0xeb9a1ab1` | `CreateFontA` |
| `0x7cf4fd7c` | `SelectObject` |
| `0x5f1ebf5d` | `SetBkColor` |
| `0x41936715` | `SetTextColor` |
| `0x805294c3` | `TextOutA` |
| `0x0dd2a6fb` | `GdiFlush` |
| `0xcc68186f` | `DeleteObject` |
| `0x9f3bef5f` | `DeleteDC` |

### Understanding the Flag Check

Once the API hashing is decoded, the `main` function (`0x1400bfb00`) becomes clear. It:

1. Creates a **Memory Device Context** via `CreateCompatibleDC`
2. Allocates a **450×50 32bpp DIB** via `CreateDIBSection`
3. Creates a **Consolas** font at size `0x18` pt via `CreateFontA`
4. Sets background to black (`0x000000`) and text color to white (`0xffffff`)
5. Reads user input and renders it into the bitmap via `TextOutA`
6. Flushes with `GdiFlush`

It then compares the resulting pixel buffer against the reference stored at `data_1400c5020`:

```c
while (true) {
    if ((var_c0[rax_22] ^ 0xaa) != *(data_1400c5020 + rax_22))
        // "Invalid flag.\n"
    rax_22 += 1;
    if (rax_22 == 0x15f90)   // 90000 bytes = 450*50*4
        // "Valid flag!\n"
}
```

Each pixel byte is **XOR'd with `0xAA`** before comparison. This means the reference data at `data_1400c5020` is simply the expected rendered bitmap XOR'd with `0xAA`.

### Extracting the Flag Statically

Since the reference bitmap is stored in the `.rdata` section, we can extract and decode it without running the binary at all.

The reference data lives at RVA `0xc5020`, inside `.rdata` (VA `0xc5000`, raw offset `0xc3600`):



Opening the resulting image reveals the flag rendered in Consolas text on a black background.

## Flag

**`srdnlen{pl5_Charles_w1n_th3_champ1on5hip}`**
