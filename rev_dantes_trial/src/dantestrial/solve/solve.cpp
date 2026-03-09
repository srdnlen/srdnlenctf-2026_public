// oracle_bruteforce.cpp
// Build: g++ -O3 -march=native -std=c++17 -pthread solve.cpp -o solve
// Usage example:
//   ./oracle 0x20A3E22B05550721 6
//   ./oracle 0x20A3E22B05550721 7 8    (L=7, threads=8)

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

// ---- Hash pieces: match your C++ logic ----

// ---- Hash pieces: match updated VM OP_MIX ----

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

// Hash as updated VM+run() does.
// - seed: low 8 bits (same as VmImage::seed & 0xFF)
// - mem_init: pointer to 256-byte memory init (pass nullptr to use all-zeros)
static inline u64 vm_final_hash(const u8* data, std::size_t len, u8 seed = 0, const u8* mem_init = nullptr)
{
    static constexpr u64 FNV_OFFSET_BASIS_64 = 0xCBF29CE484222325ull;

    // VM state needed for OP_MIX
    u64 B = 0;
    u8  dp = 0;

    // VM memory (only needed because OP_MIX reads g_mem[dp ^ seed])
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

        // absorbs (same as VM OP_MIX)
        B = fnv1a64_step(B, A);
        B = fnv1a64_step(B, dp);

        // ---- CRZ ----
        const u8 m = mem[static_cast<u8>(dp ^ seed)];
        const u8 t = crz_byte(static_cast<u8>(A ^ seed), m);

        B ^= (u64)t << ((dp & 7u) * 8u);
        B *= 0x9E3779B185EBCA87ull;
        B ^= B >> 33;

        // dp evolution
        dp = static_cast<u8>(dp + 1u + (t & 1u));
    }

    // finalize hash once VM halts (run() finalization)
    u64 h = B;
    if(h == 0ull)
        h = FNV_OFFSET_BASIS_64;

    h = fnv1a64_step(h, dp); // absorb final length (dp)
    h = fmix64(h);
    return h;
}

// ---- Oracle ----

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

// ---- Brute force engine ----

static const char* kAlphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
static constexpr std::size_t kAlphaLen = 62;

static bool increment_base62(std::vector<std::size_t>& digits, std::size_t start_pos = 0)
{
    // increments digits[start_pos..end) as a base-62 odometer
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

// Split work by fixing the first character range per thread.
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
    // Each thread gets a subset of first-character values: tid, tid+threads, ...
    std::vector<std::size_t> digits(cfg.L, 0);

    for(std::size_t first = cfg.tid; first < kAlphaLen && !cfg.found->load(std::memory_order_relaxed); first += cfg.threads)
    {
        digits[0] = first;
        for(std::size_t i = 1; i < cfg.L; ++i) digits[i] = 0;

        std::string candidate(cfg.L, 'A');

        // Iterate all suffix combinations
        while(!cfg.found->load(std::memory_order_relaxed))
        {
            digits_to_string(digits, candidate.data());

            // count attempts
            cfg.counter->fetch_add(1, std::memory_order_relaxed);

            if(cfg.oracle(candidate.data(), candidate.size()))
            {
                if(!cfg.found->exchange(true))
                {
                    *cfg.result = candidate;
                }
                return;
            }

            // increment suffix starting at position 1 (keep first fixed for this loop)
            if(!increment_base62(digits, 1))
                break;
        }
    }
}

static u64 parse_u64_hex(const std::string& s)
{
    // accepts "0x..." or plain hex
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

    // simple progress loop
    while(!found.load(std::memory_order_relaxed))
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        auto t1 = std::chrono::steady_clock::now();
        double sec = std::chrono::duration<double>(t1 - t0).count();
        u64 tries = counter.load(std::memory_order_relaxed);
        double rate = (sec > 0.0) ? (tries / sec) : 0.0;

        std::cerr << "\rtries=" << tries << " rate=" << static_cast<u64>(rate) << "/s" << std::flush;

        // stop if we've clearly exhausted all first chars (threads will end) and none found:
        bool all_done = true;
        for(auto& th : pool)
        {
            // can't directly check if thread finished without join; so we just keep waiting.
            (void)th;
            all_done = false;
            break;
        }
        (void)all_done;
        // We'll just wait until threads join below.
        // (If no match exists in the space, it will run until all threads naturally finish,
        //  and found remains false.)
        // To keep code simple, we don't implement a separate "done" counter.
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