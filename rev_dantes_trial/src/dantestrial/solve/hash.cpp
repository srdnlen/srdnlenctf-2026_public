// hash_oracle.cpp
// Build: g++ -O3 -std=c++17 hash_oracle.cpp -o hash
// Usage: ./hash "YourStringHere" [seed_hex_00_to_FF]
//
// Notes:
// - By default seed=0 and mem[256]=0, which matches your sample image (mem_len = 0).
// - If your VM image has nonzero mem_init, pass it in by editing mem_init below.

#include <cstdint>
#include <iostream>
#include <string>
#include <array>
#include <cstdlib>

using u8  = std::uint8_t;
using u64 = std::uint64_t;

static inline u64 fnv1a64_step(u64 h, u8 b)
{
    h ^= static_cast<u64>(b);
    h *= 0x100000001B3ull;   // FNV-1a 64 prime
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

// Same CRZ primitive as your VM
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

static constexpr u64 FNV_OFFSET_BASIS_64 = 0xCBF29CE484222325ull;

struct VmHashState
{
    u64 B = 0;
    u8  dp = 0;
    u8  A  = 0;
    u8  seed = 0;
    std::array<u8, 256> mem{}; // must match g_mem init
};

static inline void op_mix(VmHashState& v)
{
    if(v.B == 0ull)
        v.B = FNV_OFFSET_BASIS_64;

    // absorbs
    v.B = fnv1a64_step(v.B, v.A);
    v.B = fnv1a64_step(v.B, v.dp);

    // ---- CRZ ----
    const u8 m = v.mem[static_cast<u8>(v.dp ^ v.seed)];
    const u8 t = crz_byte(static_cast<u8>(v.A ^ v.seed), m);

    v.B ^= (u64)t << ((v.dp & 7u) * 8u);
    v.B *= 0x9E3779B185EBCA87ull;
    v.B ^= v.B >> 33;

    // dp evolution
    v.dp = static_cast<u8>(v.dp + 1u + (t & 1u));
}

u64 vm_hash(const std::string& s, u8 seed, const std::array<u8,256>& mem_init)
{
    VmHashState v;
    v.seed = seed;
    v.mem  = mem_init;
    v.dp   = 0;
    v.B    = 0;

    for(unsigned char c : s)
    {
        const u8 ch = static_cast<u8>(c);

        // match your VM newline/CR termination behavior
        if(ch == 0x0A || ch == 0x0D)
            break;

        // VM: OP_IN sets A to input byte
        v.A = ch;

        // VM: OP_MIX consumes A/dp/seed/mem and updates B/dp
        op_mix(v);
    }

    // VM finalize
    u64 h = v.B;
    if(h == 0ull)
        h = FNV_OFFSET_BASIS_64;

    h = fnv1a64_step(h, v.dp); // absorb final length (dp)
    h = fmix64(h);
    return h;
}

static u8 parse_seed_hex(const char* s)
{
    // accepts "AA" or "0xAA"
    unsigned long x = std::strtoul(s, nullptr, 16);
    return static_cast<u8>(x & 0xFFu);
}

int main(int argc, char** argv)
{
    if(argc != 2 && argc != 3)
    {
        std::cerr << "Usage: " << argv[0] << " \"string\" [seed_hex_00_to_FF]\n";
        return 1;
    }

    std::string input = argv[1];
    u8 seed = 0;
    if(argc == 3)
        seed = parse_seed_hex(argv[2]);

    // Default: all-zero mem_init (matches mem_len=0 images)
    std::array<u8,256> mem_init{};
    mem_init.fill(0);

    // If your VM image has mem_init bytes, copy them here at the start:
    // for(size_t i=0; i<mem_len; ++i) mem_init[i] = ...;

    u64 h = vm_hash(input, seed, mem_init);

    std::cout << std::hex << std::uppercase;
    std::cout << "H = 0x" << h << "\n";
    return 0;
}