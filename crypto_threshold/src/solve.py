from sage.all import *
from pwn import remote, process
from ts import TSParam, TS, RingElemVec, SerializedRingElemVec
import os, json, numpy as np, random, tqdm, collections, multiprocessing

flag = os.getenv("FLAG", "srdnlen{this_is_a_fake_flag}")

param = TSParam(N=16, T=8)
target = b"give me the flag"

me = TS(param)

io = process(["python3", "server.py"])

my_data = json.loads(
    io.recvline_contains(b"Your secret key and verification key: ").split(b": ", 1).pop()
)
me.receive_vk(my_data["vk"])
me.receive_ski(0, my_data["sk"])


def commit(my_w: SerializedRingElemVec = None):
    global me, io, param
    if my_w is None:
        my_w = me.preprocessing()
    io.sendlineafter(b"Your choice: ", b"1")
    io.sendlineafter(b"Get your preprocessing data: ", json.dumps(my_w).encode())
    for i in range(1, param.N):
        if len(me.commitment_cache[i]) >= 8:
            continue  # limit preprocessing data to avoid memory exhaustion
        line = io.recvline(False)
        assert f"Preprocessing data from signer #{i}:" in line.decode()
        wi = json.loads(line.split(b": ", 1).pop())
        me.receive_commitment(i, wi)


def get_w(S: list[int], target_w: RingElemVec) -> RingElemVec:
    global me, param
    assert param.T == len(set(S))
    ws = [me.commitment_cache[i][0] for i in S if i != me.i]
    return target_w - sum(ws)


def get_signatures(S: list[int], msg: bytes) -> list[RingElemVec]:
    global me, io, param
    
    io.sendlineafter(b"Your choice: ", b"2")
    io.sendlineafter(b"Message to sign (hex): ", msg.hex().encode())
    io.sendlineafter(
        f"Select {param.T} signers from [1-{param.N}]: ".encode(),
        " ".join(map(str, S)).encode(),
    )
    sigs = []
    for i in S:
        if i != me.i:
            line = io.recvline(False)
            assert f"Partial signature from signer #{i}:" in line.decode()
            sig = json.loads(line.split(b": ", 1).pop())
            wi, zi = map(me.unserialize, sig)
            assert np.all(wi == me.commitment_cache[i][0])
            sigs.append(sig)
    
    if me.masking_cache:
        # use my masking to sign and verify correctness
        my_sig = me.sign(S, msg)
        assert me.i == 0
        sig = me.aggregate(S, msg, [my_sig] + sigs)
        assert me.verify(msg, sig)
    else:
        # pop commitments if we forged preprocessing data
        for i in S:
            if i != me.i:
                me.commitment_cache[i].pop(0)
    
    return sigs


nsamples = 64  # number of leaks usually needed to recover one signer
to_recover = param.N - 1  # number of signers for which we want to recover nsamples leaks

assert (param.N - 1) // (param.T - 1) <= 2, \
    "The next loop requires that N-1 <= 2*(T-1)"
for _ in range(2):  # two commits to desynchronize cache
    commit()
get_signatures([0] + list(range(1, param.T)), os.urandom(16))
get_signatures([0] + list(range(param.T, 2 * param.T - 1)), os.urandom(16))

# fix a target w and message to fix the challenge c
target_w = param.Rq.uniform(param.k)
msg = os.urandom(16)
approx = lambda w: np.array([wi.high_bits(param.gamma_w) for wi in w])
seed = me.challenge_seed(msg, approx(target_w))
c = param.Rq.sample_in_ball(param.tau, seed=seed)

leaks = dict()
counter = collections.Counter()
pbar = tqdm.tqdm()
while True:
    # select a signer to recover
    S = tuple([0] + sorted(random.sample(range(1, param.N), param.T - 1)))
    while S in leaks:
        S = tuple([0] + sorted(random.sample(range(1, param.N), param.T - 1)))

    # get new leaks for set S
    my_w = get_w(S, target_w)
    commit(me.serialize(my_w))
    sigs = get_signatures(S, msg)
    ws = [me.unserialize(wi) for wi, _ in sigs]
    assert np.all(sum(ws) == target_w - my_w)
    zs = {i: me.unserialize(zi) for i, (_, zi) in zip(filter(lambda i: i != me.i, S), sigs)}
    leaks[S] = zs
    
    # check if we have enough leaks to recover T-1 signers
    for j in S:
        if j != me.i:
            counter[j] += 1
    enough = [j for j, cnt in counter.items() if cnt >= nsamples]
    pbar.update()
    pbar.set_description(f"Recovered enough leaks for {len(enough)}/{to_recover} signers (current max: #{max(counter.values())})")
    if len(enough) >= to_recover:
        break
pbar.close()


def shortest_solution(M, mod: int, weights: list[int]):
    L = Matrix.block(ZZ, [
        [1, M],
        [0, mod],
    ])
    Q = Matrix.diagonal(ZZ, weights)

    L *= Q
    L = L.LLL()
    L *= Q.inverse()

    for row in L.rows():
        row *= sgn(row[1])
        if row[1] == 1:
            return list(map(int, row))
    raise ValueError("no shortest solution found")


def recover_sk(c: RingElemVec, leaks: dict, j: int, *, d=27, verbose=True) -> RingElemVec:
    global me, param, nsamples
    W = 2**param.q.bit_length()

    if verbose:
        print(f"Recovering signer #{j}...")
    Ss = [S for S in leaks.keys() if j in S][:nsamples]
    zs: list[RingElemVec] = [leaks[S][j] for S in Ss]
    z1s = []
    for z in zs:
        z1 = []
        for zi in z:
            _, z1i = zi.power2round(d)
            z1.append(z1i)
        z1s.append(np.array(z1))
    ls = [me.lagrange_coeff(j, S) for S in Ss]

    sj = []
    for h in range(param.ell):
        coeffs = []
        for i in range(param.n):
            sol = shortest_solution(
                Matrix(ZZ, [ls, [-z1[h][i] * 2**d for z1 in z1s]]),
                param.q,
                [1, W] + [W >> d] * len(ls),
            )
            coeffs.append(sol[0] % param.q)
        
        csjh = param.Rq(coeffs)  # c * s_j[h], j-th signer's h-th entry of the vector
        rs = [z[h] - l * csjh for z, l in zip(zs, ls)]
        bound = param.sigma_w * param.n**0.5 * 1.2  # slightly larger than expected norm
        if max(r.norm(2) for r in rs) < bound:
            sjh = csjh * c.inverse()
            sj.append(sjh)
        else:
            sj.append(None)  # failed to recover
    
    if verbose:
        print(f"Signer #{j} finished ({sj.count(None)}/{param.ell} failures)")
    return np.array(sj)


# compute all lazy coeffs to avoid threading issues later
for zs in leaks.values():
    for z in zs.values():
        for zi in z:
            _ = zi.coeffs

with multiprocessing.Pool() as pool:
    sk = [me.si] + pool.starmap(
        recover_sk,
        [(c, leaks, j) for j in range(1, param.N)],
    )

sk = {i: sk[i] for i in range(16) if np.all(sk[i] != None)}
if len(sk) < param.T:
    raise ValueError("Failed to recover enough signers' secret keys")

S = list(sk.keys())[:param.T]
s = sum(me.lagrange_coeff(i, S) * sk[i] for i in S)
assert max(si.norm(2) for si in s) < param.sigma_t * param.n**0.5 * 1.2, \
    "Recovered secret key has too large norm, r bound may be incorrect"

signer = {i: TS(param) for i in sk.keys()}
for i in signer.keys():
    signer[i].receive_vk(my_data["vk"])
    signer[i].receive_ski(i, me.serialize(sk[i]))

for i in signer.keys():
    wi = signer[i].preprocessing()
    for j in signer.keys():
        if j != i:
            signer[j].receive_commitment(i, wi)

msg = target
S = list(signer.keys())[:param.T]
sigs = []
for i in S:
    sig = signer[i].sign(S, msg)
    sigs.append(sig)
sig = me.aggregate(S, msg, sigs)
assert me.verify(msg, sig)

io.sendlineafter(b"Your choice: ", b"3")
io.sendline(json.dumps(sig).encode())
try:
    io.interactive()
except (EOFError, KeyboardInterrupt):
    pass
finally:
    io.close()
