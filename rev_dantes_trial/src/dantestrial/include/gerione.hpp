#pragma once
#include <cstdint>
#include <cstddef>
#include "bn_common.h"

namespace dantes::romvm
{
    using u8  = std::uint8_t;
    using u16 = std::uint16_t;
    using u32 = std::uint32_t;

    using PutChar = void(*)(int ch, void* user);   // 0..255
    using GetChar = int(*)(void* user);            // 0..255 or -1

    // payload = code_raw[code_len] || mem_init[mem_len]
    struct __attribute__((packed, aligned(4))) VmImage
    {
        u32 magic;        // 'DVM1'
        u32 code_len;
        u32 mem_len;
        u32 seed;         // low 8 bits used
        u32 reserved_lo;  // expected hash low 32
        u32 reserved_hi;  // expected hash high 32
        u8  payload[1];
    };

    static constexpr std::size_t kCodeMax = 1024;  // <<< bigger than 256
    static constexpr std::size_t kMemSize = 256;

    BN_DATA_EWRAM static u8 g_code[kCodeMax];
    BN_DATA_EWRAM static u8 g_mem[kMemSize];

    static constexpr u8 perm16[16] =
    {
        0x0, 0x9, 0x2, 0xB,
        0x4, 0xD, 0x6, 0xF,
        0x8, 0x1, 0xA, 0x3,
        0xC, 0x5, 0xE, 0x7
    };

    enum Op : u8
    {
        OP_NOP = 0,
        OP_ADP = 1,   // dp += arg
        OP_LDA = 2,   // A = mem[dp]
        OP_STA = 3,   // mem[dp] = A
        OP_XOR = 4,   // A ^= mem[dp]
        OP_ADD = 5,   // A += mem[dp]
        OP_ROL = 6,   // A = rol8(A, arg?arg:1)
        OP_CRZ = 7,   // A = crz(A, mem[dp])
        OP_IN = 8,   // A = getc() (EOF->0)
        OP_OUT = 9,   // putc(A)
        OP_MIX = 10,  // hash lane
        OP_JZ = 11,  // if A==0 -> ip = next_u16()
        OP_JMP = 12,  // ip = next_u16()
        OP_HALT = 13,  // halt
        OP_SDP8 = 14,  // dp = next_u8()
        OP_BZ = 15
    };

    struct VM
    {
        u16 ip = 0;
        u8 dp = 0;     // "byte index" for hashing
        u8 A = 0;
        std::uint64_t B = 0;
        u8 seed = 0;
        u16 code_len = 0;
        bool halted = false;
        PutChar putc = nullptr;
        GetChar getc = nullptr;
        void* user = nullptr;
    };

    static inline u8 rol8(u8 x, unsigned r)
    {
        r &= 7u;
        return static_cast<u8>((x << r) | (x >> ((8u - r) & 7u)));
    }

    using u64 = std::uint64_t;

    static inline u64 fnv1a64_step(u64 h, u8 b)
    {
        // FNV-1a 64-bit
        h ^= static_cast<u64>(b);
        h *= 0x100000001B3ull; // FNV prime
        return h;
    }

    static inline u64 fmix64(u64 k)
    {
        // MurmurHash3 fmix64
        k ^= k >> 33;
        k *= 0xFF51AFD7ED558CCDull;
        k ^= k >> 33;
        k *= 0xC4CEB9FE1A85EC53ull;
        k ^= k >> 33;
        return k;
    }

    static inline u8 sbox(u8 x) // bijection mod 256
    {
        return static_cast<u8>(x * 29u + 37u);
    }

    static inline u8 crz_byte(u8 a, u8 b)
    {
        static constexpr u8 MAP[3][3] =
        {
            { 1, 0, 0 },
            { 1, 0, 2 },
            { 2, 2, 1 },
        };

        u8 out = 0, pow = 1;
        for(int i = 0; i < 6; ++i)
        {
            const u8 ta = static_cast<u8>(a % 3u);
            const u8 tb = static_cast<u8>(b % 3u);
            a = static_cast<u8>(a / 3u);
            b = static_cast<u8>(b / 3u);

            out = static_cast<u8>(out + MAP[ta][tb] * pow);
            pow = static_cast<u8>(pow * 3u);
        }
        return out;
    }

    static inline u8 fetch_decoded(VM& v)
    {
        if(v.ip >= v.code_len || v.ip >= kCodeMax)
        {
            v.halted = true;
            return 0;
        }

        const u16 pos = v.ip;
        const u8  raw = g_code[pos];
        
        const u8 key = static_cast<u8>((pos * 13u + v.seed + 0x5Au) & 0xFFu);
        const u8 dec = static_cast<u8>(raw ^ key);

        v.ip = static_cast<u16>(pos + 1u);
        return dec;
    }

    static inline u16 fetch_u16(VM& v)
    {
        const u16 lo = fetch_decoded(v);
        const u16 hi = fetch_decoded(v);
        return static_cast<u16>(lo | (hi << 8));
    }

    static inline void step(VM& v)
    {
        if(v.halted)
            return;

        const u8 dec = fetch_decoded(v);
        const u8 op  = perm16[dec & 0x0Fu];
        const u8 arg = static_cast<u8>(dec >> 4);

        switch(op)
        {
            case OP_NOP: break;

            case OP_ADP: v.dp = static_cast<u8>(v.dp + arg); break;

            case OP_LDA: v.A = g_mem[v.dp]; break;
            case OP_STA: g_mem[v.dp] = v.A; break;

            case OP_XOR: v.A = static_cast<u8>(v.A ^ g_mem[v.dp]); break;
            case OP_ADD: v.A = static_cast<u8>(v.A + g_mem[v.dp]); break;
            case OP_ROL: v.A = rol8(v.A, arg ? arg : 1u); break;

            case OP_CRZ: v.A = crz_byte(v.A, g_mem[v.dp]); break;

            case OP_MIX:
            {
                if(v.B == 0ull) v.B = 0xCBF29CE484222325ull;

                // absorbs
                v.B = fnv1a64_step(v.B, v.A);
                v.B = fnv1a64_step(v.B, v.dp);

                // ---- CRZ ----
                const u8 m = g_mem[(u8)(v.dp ^ v.seed)];
                const u8 t = crz_byte((u8)(v.A ^ v.seed), m);

                v.B ^= (u64)t << ((v.dp & 7u) * 8u);
                v.B *= 0x9E3779B185EBCA87ull;
                v.B ^= v.B >> 33;

                // dp evolution
                v.dp = (u8)(v.dp + 1u + (t & 1u));
                break;
            }

            case OP_IN:
            {
                int x = -1;
                if(v.getc) x = v.getc(v.user);

                if(x < 0) v.A = 0u;
                else
                {
                    const u8 ch = static_cast<u8>(x & 0xFF);
                    // Treat newline/CR as end-of-input sentinel
                    v.A = ch;
                }
                break;
            }

            case OP_OUT:
                if(v.putc) v.putc(static_cast<int>(v.A), v.user);
                break;

            case OP_JZ:
            {
                const u16 tgt = fetch_u16(v);
                if(v.A == 0u)
                {
                    if(tgt < v.code_len) v.ip = tgt;
                    else v.halted = true;
                }
                break;
            }

            case OP_JMP:
            {
                const u16 tgt = fetch_u16(v);
                if(tgt < v.code_len) v.ip = tgt;
                else v.halted = true;
                break;
            }

            case OP_SDP8:
                v.dp = fetch_decoded(v);
                break;

            case OP_BZ:
                v.A = (v.B == 0u) ? 0u : 1u;
                break;

            case OP_HALT:
            default:
                v.halted = true;
                break;
        }
    }

    static inline bool run(const VmImage* img, PutChar putc, GetChar getc, void* user, int max_steps = 50000)
    {
        if(!img || img->magic != 0x314D5644u)
            return false;

        if(img->code_len > kCodeMax || img->mem_len > kMemSize)
            return false;

        const u8* code_raw = img->payload;
        const u8* mem_init = img->payload + img->code_len;

        for(std::size_t i = 0; i < kCodeMax; ++i) g_code[i] = 0;
        for(std::size_t i = 0; i < kMemSize; ++i) g_mem[i] = 0;

        for(u32 i = 0; i < img->code_len; ++i) g_code[i] = code_raw[i];
        for(u32 i = 0; i < img->mem_len; ++i) g_mem[i] = mem_init[i];

        VM v;
        v.seed = static_cast<u8>(img->seed & 0xFFu);
        v.code_len = static_cast<u16>(img->code_len);
        v.putc = putc;
        v.getc = getc;
        v.user = user;
        v.dp = 0; // reset hash index/length

        for(int i = 0; i < max_steps && !v.halted; ++i)
            step(v);

        // finalize hash once VM halts
        // finalize hash once VM halts
        u64 h = v.B;
        if(h == 0ull) h = 0xCBF29CE484222325ull;

        // absorb final length (dp)
        h = fnv1a64_step(h, v.dp);

        // avalanche
        h = fmix64(h);

        // expected 64-bit from header
        const u64 expected = (static_cast<u64>(img->reserved_hi) << 32) |
                            static_cast<u64>(img->reserved_lo);

        bool ok = v.halted && (h == expected);

        /*
        if(putc)
        {
            auto hex64 = [](u64 x, PutChar p, void* u){
                const char* d = "0123456789ABCDEF";
                for(int i = 15; i >= 0; --i)
                    p(d[(x >> (i * 4)) & 0xFULL], u);
            };

            putc('H', user); putc('=', user); hex64(h, putc, user);
            putc(' ', user);
            putc('E', user); putc('=', user); hex64(expected, putc, user);
        }
        */
        
        if(ok && putc)
        {
            const char* msg = "Thou art correcteth.";
            for(const char* p = msg; *p; ++p)
                putc(*p, user);
        }

        return ok;
    }

    alignas(4) const unsigned char MB_IMAGE_CHALLENGE[] = {
        0x44, 0x56, 0x4D, 0x31, 0xA9, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x93, 0xCD, 0xB4, 0xD9, 0xCB, 0xEB, 0xF3, 0x73,
        0x52, 0x64, 0x7C, 0x81, 0x84, 0x97, 0xA8, 0xB5, 0xC7, 0x1A, 0x29, 0x48,
        0x23, 0x1F, 0xEB, 0xE8, 0x38, 0x34, 0x3E, 0x58, 0x07, 0x72, 0xD4, 0x8F,
        0x77, 0x23, 0xE8, 0x22, 0xE0, 0xE0, 0x43, 0xED, 0x78, 0x01, 0xCA, 0xAA,
        0x5D, 0xCA, 0x7F, 0x8A, 0xE5, 0xDC, 0x66, 0x81, 0x09, 0xB7, 0x1D, 0x88,
        0x30, 0xAD, 0x7F, 0x68, 0x48, 0x98, 0x1D, 0x9F, 0x2A, 0xF8, 0x34, 0xA0,
        0x68, 0x33, 0x14, 0x40, 0x1B, 0x3B, 0xF5, 0xD5, 0x62, 0x11, 0x77, 0x0A,
        0x1D, 0xEE, 0xA9, 0x7D, 0x4A, 0xA2, 0x5A, 0x9A, 0x89, 0xC5, 0x00, 0x4C,
        0x22, 0xFE, 0x85, 0x9D, 0x36, 0x1F, 0xB4, 0xE1, 0x78, 0x07, 0x0B, 0xA5,
        0x33, 0x25, 0xDF, 0x01, 0xA5, 0x2F, 0xC1, 0x8F, 0x65, 0x37, 0x60, 0x94,
        0x5E, 0x51, 0x31, 0x01, 0xA1, 0x98, 0xB4, 0xF3, 0xB1, 0xB4, 0x3E, 0x04,
        0xCE, 0xAF, 0xF2, 0xB8, 0xBD, 0xE0, 0x9C, 0xD1, 0x51, 0xF7, 0x77, 0xDD,
        0xC7, 0x14, 0x96, 0xD3, 0x5B, 0x26, 0xA9, 0xE6, 0x68, 0x19, 0xEA, 0xE1,
        0xA2, 0x17, 0x47, 0xD0, 0xF0, 0x98, 0x70, 0xCF, 0xDD, 0xD5, 0x6E, 0x9C,
        0xE9, 0x95, 0x90, 0xDD, 0x91, 0xA1, 0x42, 0xBE, 0x56, 0x9F, 0x1C, 0xCF,
        0x73,
    };

    static inline const VmImage* challenge_image()
    {
        return reinterpret_cast<const VmImage*>(MB_IMAGE_CHALLENGE);
    }
}