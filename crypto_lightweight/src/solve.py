from pwn import remote, process, context
import tqdm, itertools

max_queries = 1 << 16


def batch_encrypt(
        diff: int, nqueries: int, batch_size: int = 2**8, verbose: bool = False
    ) -> list[int]:
    global io, max_queries
    if verbose:
        range_ = tqdm.trange(0, nqueries, batch_size, desc="Encrypting batches")
    else:
        range_ = range(0, nqueries, batch_size)
    data = []
    for i in range_:
        max_queries -= min(batch_size, nqueries - i)
        if max_queries < 0:
            io.close()
            raise ValueError(f"Exceeded maximum number of queries by {abs(max_queries)}")
        io.send(f"{diff:032x}\n".encode() * min(batch_size, nqueries - i))
        for _ in range(min(batch_size, nqueries - i)):
            line = io.recvline().strip().decode()
            assert len(line) == 32, f"Expected 32 hex characters, got: {line}"
            nonce = int(line, 16)
            line = io.recvline().strip().decode()
            assert len(line) == 32, f"Expected 32 hex characters, got: {line}"
            out1 = int(line, 16)
            line = io.recvline().strip().decode()
            assert len(line) == 32, f"Expected 32 hex characters, got: {line}"
            out2 = int(line, 16)
            data.append((diff, nonce, out1, out2))
    return data


iv = 0x7372646e6c656e21
rc0 = 0x0000000000000073
rrot = lambda x, n: (x >> n) | (x << (64 - n)) & 0xffffffffffffffff
nqueries = 1 << 9

# see test.py for how these values were determined
dl_distinguishers = [
    {
        "diff": (0x8000000000000000, 0x8000000000000000),
        "mask": (0x2db36f2549927b69, 0x92b573be8bc1c7b3),
        "bias": [
            0.5,  # bias when k=00
            0.0,  # bias when k=01
            0.0,  # bias when k=10
            0.0,  # bias when k=11
        ]
    },
    {
        "diff": (0x8000000000000000, 0x8000000000000000),
        "mask": (0x96da496ddb493244, 0x0000000000000000),
        "bias": [
            0.5,   # bias when k=00
            -0.25, # bias when k=01
            -0.25, # bias when k=10
            0.5,   # bias when k=11
        ]
    },
    {
        "diff": (0x8000000000000000, 0x8000000000000000),
        "mask": (0x496da496ddb49324, 0xd37110f752d23e65),
        "bias": [
            0.37,  # bias when k=00
            0.37,  # bias when k=01
            0.58,  # bias when k=10
            0.58,  # bias when k=11
        ]
    }
]

key = [
    set(range(64)),  # k=00
    set(range(64)),  # k=01
    set(range(64)),  # k=10
    set(range(64)),  # k=11
]

diffs = set(d["diff"] for d in dl_distinguishers)
assert len(diffs) == 1, \
    "All distinguishers should have the same input difference for simplicity"
original_diff = diffs.pop()

context.log_level = "info"
io = process('./server')

diff0, diff1 = original_diff
for idx in tqdm.trange(64, desc="Iterating over all bit positions"):
    diff = rrot(diff0, idx) << 64 | rrot(diff1, idx)
    data = batch_encrypt(diff, nqueries, verbose=False)
    for dist in dl_distinguishers:
        assert dist["diff"] == (diff0, diff1), \
            f"Expected distinguisher diff to be {(diff0, diff1)}, got {dist['diff']}"
        mask0, mask1 = dist["mask"]
        mask = rrot(mask0, idx) << 64 | rrot(mask1, idx)

        cnt = 0
        for _, _, out1, out2 in data:
            if ((out1 ^ out2) & mask).bit_count() & 1 == 0:
                cnt += 1
            else:
                cnt -= 1
        bias = cnt / nqueries

        k_min = min(range(4), key=lambda k: abs(bias - dist["bias"][k]))
        c = rc0 >> (63 - idx) & 1
        for k in range(4):
            if dist["bias"][k] != dist["bias"][k_min]:
                key[k ^ c].discard(idx)

k00, k01, k10, k11 = key
if any(x & y for x, y in itertools.combinations(key, 2)):
    io.close()
    raise ValueError("Expected the sets to be disjoint")
if k00 | k01 | k10 | k11 != set(range(64)):
    io.close()
    raise ValueError("Expected the sets to cover all bit positions")

key = [None] * 128
for i in k00:
    key[i] = 0
    key[i + 64] = 0
for i in k01:
    key[i] = 0
    key[i + 64] = 1
for i in k10:
    key[i] = 1
    key[i + 64] = 0
for i in k11:
    key[i] = 1
    key[i + 64] = 1
key = int("".join(map(str, key)), 2)

if max_queries > 0:
    io.sendline(f"{0:032x}".encode())  # break the server's loop
io.sendline(f"{key:032x}".encode())
try:
    io.interactive()
except (EOFError, KeyboardInterrupt):
    pass
finally:
    io.close()
