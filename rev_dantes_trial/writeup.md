# Dante's Trial

- **Category:** Reverse
- **Solves:** 43
- **Tag:** None

## Description

And at last, Dante faced the Ferocious Beast. 
Will they be able to tr(ea)it it?

Note: the submitted flag should be enclosed in srdnlen{}.

## Details

The challenge presented is a GBA game created with the `Butano Engine` (inferable from the used classes and structures). 
The only interactable asset requests for a password, that can be inputted with a visual keyboard. 
Solve-wise, the idea is to get the address of the password check with a debugger, such as `mgba GDB Server`, and then continue reversing statically or dynamically the specific checks. 
Once you got access to the right address/function (preferably reverse statically with Ghidra GBA plugin), it's evident that the check is being performed by a VM via a hashing function (i.e. the inputted password should have the same VM hash as the correct password).
The only step left is to reverse the VM operations and execute them according to the given VM code (that is artificially bloated with appended operations that will never get executed).
The VM maintains a 64-bit state used as a rolling hash. The `MIX` (OPCODE 10) instruction updates this state by absorbing the current accumulator and data pointer using **FNV-1a**, then applying additional mixing with a custom nonlinear `CRZ` (that uses malbolge trits :D ) transform and multiplication by a large constant.

Conceptually:

```
B = FNV1a(B, A)
B = FNV1a(B, dp)

t = CRZ(A ^ seed, mem[dp ^ seed])

B ^= t << ((dp & 7) * 8)
B *= 0x9E3779B185EBCA87
B ^= B >> 33
```

When the VM halts, the final digest is produced by absorbing the final `dp` and applying the **MurmurHash3 `fmix64`**.
Straightforwardly, knowing all this, you can craft a brute-force script that, hoping for a reasonable length, will return the correct string (in this case, the length was 6: you would have discoreved that by running the script for increasing lengths).

## Solution
```cpp
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>

using u8  = std::uint8_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;

static inline u64 fnv1a64_step(u64 h, u8 b)
{
    h ^= static_cast<u64>(b);
    h *= 0x100000001B3ull;
    return h;
}

static inline u64 fmix64(u64 k)
{
    k ^= k >> 33;
    k *= 0xFF51AFD7ED558CCDull;
    k ^= k >> 33;
    k *= 0xC4CEB9FE1A85EC53ull;
    k ^= k >> 33;
    return k;
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

static inline u64 vm_final_hash(const u8* data, std::size_t len, u8 seed = 0, const u8* mem_init = nullptr)
{
    static constexpr u64 FNV_OFFSET_BASIS_64 = 0xCBF29CE484222325ull;

    // VM state for OP_MIX
    u64 B = 0;
    u8 dp = 0;

    // VM memory
    u8 mem[256];
    if(mem_init)
        std::memcpy(mem, mem_init, 256);
    else
        std::memset(mem, 0, 256);

    for(std::size_t i = 0; i < len; ++i)
    {
        const u8 A = data[i];
        if(A == 0x0A || A == 0x0D)
            break;

        if(B == 0ull)
            B = FNV_OFFSET_BASIS_64;

        // VM OP_MIX
        B = fnv1a64_step(B, A);
        B = fnv1a64_step(B, dp);

        // CRZ
        const u8 m = mem[static_cast<u8>(dp ^ seed)];
        const u8 t = crz_byte(static_cast<u8>(A ^ seed), m);

        B ^= (u64)t << ((dp & 7u) * 8u);
        B *= 0x9E3779B185EBCA87ull;
        B ^= B >> 33;

        // dp evolution
        dp = static_cast<u8>(dp + 1u + (t & 1u));
    }

    // finalize hash
    u64 h = B;
    if(h == 0ull)
        h = FNV_OFFSET_BASIS_64;

    h = fnv1a64_step(h, dp); // final length (dp)
    h = fmix64(h);
    return h;
}

struct Oracle
{
    u64 target;

    bool operator()(const std::string& s) const
    {
        return vm_final_hash(reinterpret_cast<const u8*>(s.data()), s.size()) == target;
    }

    bool operator()(const char* s, std::size_t len) const
    {
        return vm_final_hash(reinterpret_cast<const u8*>(s), len) == target;
    }
};

// ---- Brute Force Time :) ----

static const char* kAlphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
static constexpr std::size_t kAlphaLen = 62;

static bool increment_base62(std::vector<std::size_t>& digits, std::size_t start_pos = 0)
{
    for(std::size_t i = start_pos; i < digits.size(); ++i)
    {
        digits[i]++;
        if(digits[i] < kAlphaLen) return true;
        digits[i] = 0;
    }
    return false; // overflow
}

static void digits_to_string(const std::vector<std::size_t>& digits, char* out)
{
    for(std::size_t i = 0; i < digits.size(); ++i)
        out[i] = kAlphabet[digits[i]];
}

struct WorkerConfig
{
    int tid;
    int threads;
    std::size_t L;
    Oracle oracle;
    std::atomic<bool>* found;
    std::string* result;
    std::atomic<u64>* counter;
};

static void worker(WorkerConfig cfg)
{
    std::vector<std::size_t> digits(cfg.L, 0);

    for(std::size_t first = cfg.tid; first < kAlphaLen && !cfg.found->load(std::memory_order_relaxed); first += cfg.threads)
    {
        digits[0] = first;
        for(std::size_t i = 1; i < cfg.L; ++i) digits[i] = 0;

        std::string candidate(cfg.L, 'A');

        while(!cfg.found->load(std::memory_order_relaxed))
        {
            digits_to_string(digits, candidate.data());

            cfg.counter->fetch_add(1, std::memory_order_relaxed);

            if(cfg.oracle(candidate.data(), candidate.size()))
            {
                if(!cfg.found->exchange(true))
                {
                    *cfg.result = candidate;
                }
                return;
            }

            if(!increment_base62(digits, 1))
                break;
        }
    }
}

static u64 parse_u64_hex(const std::string& s)
{
    std::size_t idx = 0;
    u64 v = 0;
    if(s.rfind("0x", 0) == 0 || s.rfind("0X", 0) == 0) idx = 2;
    for(; idx < s.size(); ++idx)
    {
        char c = s[idx];
        int d = -1;
        if(c >= '0' && c <= '9') d = c - '0';
        else if(c >= 'a' && c <= 'f') d = 10 + (c - 'a');
        else if(c >= 'A' && c <= 'F') d = 10 + (c - 'A');
        else continue;
        v = (v << 4) | static_cast<u64>(d);
    }
    return v;
}

int main(int argc, char** argv)
{
    if(argc < 3)
    {
        std::cerr << "Usage: " << argv[0] << " <target_hex_u64> <length_L> [threads]\n"
                  << "Example: " << argv[0] << " 0x20A3E22B05550721 6 8\n";
        return 1;
    }

    const u64 target = parse_u64_hex(argv[1]);
    const std::size_t L = static_cast<std::size_t>(std::stoul(argv[2]));
    const int threads = (argc >= 4) ? std::max(1, std::stoi(argv[3])) : std::max(1u, std::thread::hardware_concurrency());

    if(L == 0)
    {
        std::cerr << "Length must be > 0\n";
        return 1;
    }
    if(L > 64)
    {
        std::cerr << "Refusing L > 64 (too large)\n";
        return 1;
    }

    Oracle oracle{target};

    std::atomic<bool> found{false};
    std::string result;
    std::atomic<u64> counter{0};

    std::vector<std::thread> pool;
    pool.reserve(threads);

    auto t0 = std::chrono::steady_clock::now();

    for(int tid = 0; tid < threads; ++tid)
    {
        WorkerConfig cfg;
        cfg.tid = tid;
        cfg.threads = threads;
        cfg.L = L;
        cfg.oracle = oracle;
        cfg.found = &found;
        cfg.result = &result;
        cfg.counter = &counter;
        pool.emplace_back(worker, cfg);
    }

    while(!found.load(std::memory_order_relaxed))
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        auto t1 = std::chrono::steady_clock::now();
        double sec = std::chrono::duration<double>(t1 - t0).count();
        u64 tries = counter.load(std::memory_order_relaxed);
        double rate = (sec > 0.0) ? (tries / sec) : 0.0;

        std::cerr << "\rtries=" << tries << " rate=" << static_cast<u64>(rate) << "/s" << std::flush;

        bool all_done = true;
        for(auto& th : pool)
        {
            (void)th;
            all_done = false;
            break;
        }
        (void)all_done;
    }

    for(auto& th : pool) th.join();

    std::cerr << "\n";

    if(found.load())
    {
        std::cout << "FOUND: " << result << "\n";
        std::cout << "hash = 0x" << std::hex << vm_final_hash(reinterpret_cast<const u8*>(result.data()), result.size()) << std::dec << "\n";
        return 0;
    }
    else
    {
        std::cout << "No match found in alnum^" << L << " for target 0x" << std::hex << target << std::dec << "\n";
        return 2;
    }
}
```