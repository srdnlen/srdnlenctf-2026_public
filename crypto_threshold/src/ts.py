from dataclasses import dataclass
from functools import cached_property
import numpy as np, hashlib, math

from ring import Ring, RingElem


@dataclass(frozen=True)
class TSParam:
    q: int = 2146959361  # prime s.t. 2n | (q-1), q-1 has small factors and q is less than and near 2^31
    n: int = 256  # power of two
    sigma_t: float = 2.0**8  # standard deviation for Gaussian sampling of secret and error polynomials
    sigma_w: float = 2.0**22  # standard deviation for Gaussian sampling of masking polynomial
    gamma_w: int = (q - 1) // 2**8  # bit dropping performed on aggregated commitment
    k: int = 6  # number of rows of public matrix A
    ell: int = 5  # number of columns of public matrix A
    tau: int = 39  # hamming weight for sparse challenge polynomial
    N: int = None  # number of signers
    T: int = None  # threshold

    def __post_init__(self):
        if self.N is None:
            raise ValueError("N must be specified")
        if self.T is None:
            raise ValueError("T must be specified")
        if not (1 <= self.T <= self.N):
            raise ValueError("T must be in the range [1, N]")

    @cached_property
    def Rq(self) -> Ring:
        return Ring(n=self.n, q=self.q)
    
    @cached_property
    def B(self) -> float:
        return self.T * self.sigma_w * self.n**0.5


RingElemVec = np.ndarray[RingElem]
SerializedRingElemVec = list[str]

VK = tuple[str, SerializedRingElemVec]
SK = list[SerializedRingElemVec]
PartialSign = tuple[SerializedRingElemVec, SerializedRingElemVec]
Sign = tuple[str, SerializedRingElemVec, SerializedRingElemVec]


class TS:
    """ Threshold Signature Scheme from https://eprint.iacr.org/2024/496.pdf """

    def __init__(self, param: TSParam, *, serialize_ntt: bool = True):
        self.param = param
        # whether to serialize in NTT domain (default True for efficiency, due to RingElem implementation)
        self.serialize_ntt = serialize_ntt
        self.masking_cache: list[RingElemVec] = []
        self.commitment_cache = [[] for _ in range(param.N)]
        self.rho: bytes = None
        self.A: RingElemVec = None
        self.t: RingElemVec = None
        self.i: int = None
        self.si: RingElemVec = None
    
    def serialize(self, x: RingElemVec, *, hex: bool = True) -> SerializedRingElemVec:
        ntt = self.serialize_ntt
        if hex:
            return list(map(lambda y: RingElem.to_bytes(y, ntt=ntt).hex(), x))
        else:
            return list(map(lambda y: RingElem.to_bytes(y, ntt=ntt), x))

    def unserialize(self, x: SerializedRingElemVec, *, hex: bool = True) -> RingElemVec:
        Rq = self.param.Rq
        ntt = self.serialize_ntt
        if hex:
            return np.array([Rq.from_bytes(bytes.fromhex(y), ntt=ntt) for y in x])
        else:
            return np.array([Rq.from_bytes(y, ntt=ntt) for y in x])

    def receive_vk(self, vk: VK) -> tuple[RingElemVec, RingElemVec]:
        assert self.rho is None and self.A is None and self.t is None, "VK already received"
        param = self.param
        rho, t = vk
        assert isinstance(rho, str), "invalid rho format"
        assert len(t) == param.k, "invalid t length"
        assert all(isinstance(x, str) for x in t), "invalid t format"
        self.rho = bytes.fromhex(rho)
        self.A = param.Rq.uniform((param.k, param.ell), seed=self.rho, ntt=True)
        self.t = self.unserialize(t)
        return self.A, self.t
    
    def receive_ski(self, i: int, ski: SerializedRingElemVec) -> RingElemVec:
        assert self.i is None and self.si is None, "partial sk already received"
        assert 0 <= i < self.param.N, "invalid signer index"
        assert len(ski) == self.param.ell, "invalid partial sk length"
        assert all(isinstance(x, str) for x in ski), "invalid partial sk format"
        self.i = i
        self.si = self.unserialize(ski)
        return self.si
    
    def receive_commitment(self, j: int, w: SerializedRingElemVec) -> RingElemVec:
        assert 0 <= j < self.param.N, "invalid signer index"
        assert self.i != j, "cannot receive own commitment"
        assert len(w) == self.param.k, "invalid commitment length"
        assert all(isinstance(x, str) for x in w), "invalid commitment format"
        w = self.unserialize(w)
        self.commitment_cache[j].append(w)
        return w
    
    def challenge_seed(self, msg: bytes, w: RingElemVec) -> bytes:
        seed = hashlib.sha3_512(
            hashlib.sha3_512(self.rho + b"".join(self.serialize(self.t, hex=False))).digest() +
            hashlib.sha3_512(msg).digest() +
            hashlib.sha3_512(b"".join(self.serialize(w, hex=False))).digest()
        ).digest()
        return seed
    
    def lagrange_coeff(self, i: int, S: list[int]) -> int:
        assert i in S, "i must be in S"
        assert len(S) == self.param.T, "S must have size T"
        assert len(set(S)) == self.param.T, "S must have distinct indices"
        # asumes 0-based indexing for i and S, so convert to 1-based indexing
        i = i + 1
        S0 = iter(j + 1 for j in S)
        S1 = iter(j + 1 for j in S)
        q = self.param.q
        num = math.prod(-j for j in S0 if j != i) % q
        den = math.prod((i - j) % q for j in S1 if j != i) % q
        return (num * pow(den, -1, q)) % q
    
    def keygen(self, seed: bytes) -> tuple[VK, SK]:
        param = self.param
        Rq = param.Rq

        def prg(data: bytes):
            nonlocal param
            data = hashlib.sha3_512(data).digest() + \
                int.to_bytes(param.N, 2, "little") + int.to_bytes(param.T, 2, "little")
            for cnt in range(1 << 16):
                yield hashlib.sha3_512(data + int.to_bytes(cnt, 2, "little")).digest()
            raise ValueError("prg: too many requests")

        gen = prg(seed)

        rho = next(gen)
        A = Rq.uniform((param.k, param.ell), seed=rho, ntt=True)
        s = Rq.gaussian(param.sigma_t, param.ell, seed=next(gen))
        e = Rq.gaussian(param.sigma_t, param.k, seed=next(gen))
        t = A @ s + e  # no truncation, just for simplicity, no security impact
        
        poly_eval = lambda poly, x: sum(c * pow(x, i, param.q) for i, c in enumerate(poly))
        poly = Rq.uniform((param.T - 1, param.ell), seed=next(gen))
        poly = np.vstack([s, poly])  # constant term is s
        ss = [poly_eval(poly, i) for i in range(1, param.N + 1)]

        vk = (rho.hex(), self.serialize(t))
        sk = [self.serialize(si) for si in ss]
        return vk, sk
    
    def preprocessing(self) -> SerializedRingElemVec:
        param = self.param
        Rq = param.Rq
        r = Rq.gaussian(param.sigma_w, param.ell)
        e = Rq.gaussian(param.sigma_w, param.k)
        w = self.A @ r + e
        self.masking_cache.append(r)
        self.commitment_cache[self.i].append(w)
        return self.serialize(w)

    def sign(self, S: list[int], msg: bytes) -> PartialSign:
        param = self.param
        assert len(S) == param.T, "S must have size T"
        assert len(set(S)) == param.T, "S must have distinct indices"
        assert self.i in S, "own index must be in S"
        assert all(0 <= j < param.N for j in S), "invalid signer index in S"
        assert all(len(self.commitment_cache[j]) > 0 for j in S), \
            "commitments from all signers in S must be received"
        
        approx = lambda w: np.array([wi.high_bits(param.gamma_w) for wi in w])
        wi = self.commitment_cache[self.i][0]
        w = approx(sum(self.commitment_cache[j].pop(0) for j in S))
        
        seed = self.challenge_seed(msg, w)
        c = param.Rq.sample_in_ball(param.tau, seed=seed)

        r = self.masking_cache.pop(0)
        z = r + c * self.lagrange_coeff(self.i, S) * self.si

        return self.serialize(wi), self.serialize(z)
    
    def aggregate(self, S: list[int], msg: bytes, sigs: list[PartialSign]) -> Sign:
        param = self.param
        assert len(sigs) == param.T, "number of partial signatures must be T"
        assert len(S) == param.T, "S must have size T"
        assert len(set(S)) == param.T, "S must have distinct indices"
        assert all(0 <= j < param.N for j in S), "invalid signer index in S"

        ws = [self.unserialize(wi) for wi, _ in sigs]
        zs = [self.unserialize(zi) for _, zi in sigs]

        approx = lambda w: np.array([wi.high_bits(param.gamma_w) for wi in w])
        w = approx(sum(ws))
        z = sum(zs)

        seed = self.challenge_seed(msg, w)
        c = param.Rq.sample_in_ball(param.tau, seed=seed)

        y = approx(self.A @ z - c * self.t)
        h = w - y

        return seed.hex(), self.serialize(z), self.serialize(h)

    def verify(self, msg: bytes, sig: Sign) -> bool:
        param = self.param
        
        seed, z, h = sig
        seed = bytes.fromhex(seed)
        z = self.unserialize(z)
        h = self.unserialize(h)

        norm2 = lambda v: max([vi.norm(2) for vi in v])
        if norm2(z) > param.B:
            return False
        if norm2(h * (2 * param.gamma_w)) > param.B:
            return False

        c = param.Rq.sample_in_ball(param.tau, seed=seed)
        approx = lambda w: np.array([wi.high_bits(param.gamma_w) for wi in w])
        w = approx(self.A @ z - c * self.t) + h
        return seed == self.challenge_seed(msg, w)


if __name__ == "__main__":
    import os, random, time

    param = TSParam(N=16, T=8)

    print(f"Threshold Signature Scheme Test for N={param.N}, T={param.T}")
    start = time.time()

    # Key generation phase
    trusted = TS(param)
    tick = time.time()
    vk, sk = trusted.keygen(os.urandom(32))
    tock = time.time()
    print(f"Key generation time: {tock - tick:.3f}")
    trusted.receive_vk(vk)
    
    # Key distribution phase
    signer = [TS(param) for _ in range(param.N)]
    for i in range(param.N):
        signer[i].receive_vk(vk)
        signer[i].receive_ski(i, sk[i])
    
    # Preprocessing phase
    times = []
    for i in range(param.N):
        tick = time.time()
        wi = signer[i].preprocessing()
        tock = time.time()
        times.append(tock - tick)
        for j in range(param.N):
            if i != j:
                signer[j].receive_commitment(i, wi)
    print(f"Preprocessing time per signer: {sum(times)/param.N:.3f} sec (max: {max(times):.3f} sec)")
    
    # Individual signing phase
    msg = os.urandom(32)
    S = random.sample(range(param.N), param.T)
    sigs, times = [], []
    for i in S:
        tick = time.time()
        sigi = signer[i].sign(S, msg)
        tock = time.time()
        times.append(tock - tick)
        sigs.append(sigi)
    print(f"Signing time per signer: {sum(times)/param.T:.3f} sec (max: {max(times):.3f} sec)")

    # Signature aggregation phase
    tick = time.time()
    sig = trusted.aggregate(S, msg, sigs)
    tock = time.time()
    print(f"Signature aggregation time: {tock - tick:.3f} sec")
    
    # Signature verification phase
    tick = time.time()
    res = trusted.verify(msg, sig)
    tock = time.time()
    print(f"Signature verification time: {tock - tick:.3f} sec")
    
    assert res, "Signature verification failed, but it should have succeeded"
    print("Signature verification succeeded")
    
    end = time.time()
    print(f"Total time: {end - start:.3f} sec")
