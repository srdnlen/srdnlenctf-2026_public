# No intended vulnerability here

from random import SystemRandom
from crypto_random import CryptoRandom
import dataclasses, functools, numpy as np, gmpy2

__all__ = ["Ring", "RingElem"]


@dataclasses.dataclass(frozen=True)
class Ring:
    q: int
    n: int

    def __post_init__(self):
        if self.q < 0 or self.q >= 1 << 31:
            raise ValueError(f"q must be in [0, 2^31), got {self.q}")
        if not gmpy2.is_prime(self.q):
            raise ValueError(f"q must be prime, got {self.q}")
        if self.n & (self.n - 1) != 0 or self.n < 2:
            raise ValueError(f"n must be a power of two, got {self.n}")
        if (self.q - 1) % (2 * self.n) != 0:
            raise ValueError(f"q - 1 must be divisible by 2*n")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Ring):
            return False
        return self.q == other.q and self.n == other.n
    
    def __ne__(self, other) -> bool:
        return not (self == other)
    
    def __call__(self, value) -> "RingElem":
        if isinstance(value, RingElem):
            if value.ring != self:
                raise ValueError("cannot coerce RingElem from different ring")
            return value
        if hasattr(value, "__int__"):
            value = int(value)
            return RingElem(
                self, 
                coeffs=np.array([value % self.q] + [0] * (self.n - 1)),
                evals=np.array([value % self.q] * self.n)
            )
        if isinstance(value, (list, tuple)) and len(value) == self.n and all(hasattr(v, "__int__") for v in value):
            value = np.array([x % self.q for x in value], dtype=np.int64)
        if isinstance(value, np.ndarray) and value.shape == (self.n,):
            return RingElem(self, coeffs=value)
        raise TypeError(f"conversion from {type(value).__name__} to RingElem not supported")
    
    def __repr__(self) -> str:
        return f"Ring(q={self.q}, n={self.n})"
    
    __str__ = __repr__

    def gaussian(self, stddev: float, shape: int | tuple = None, *, seed=None) -> "RingElem | np.ndarray[RingElem]":
        if stddev <= 0:
            raise ValueError(f"stddev must be positive, got {stddev}")
        rng = SystemRandom() if seed is None else CryptoRandom(seed)
        get_coeffs = lambda: np.array(
            [int(round(rng.gauss(0, stddev))) % self.q for _ in range(self.n)],
            dtype=np.int64
        )
        if shape is None:
            return RingElem(self, coeffs=get_coeffs())
        elems = np.empty(shape, dtype=object)
        for idx in np.ndindex(shape):
            elems[idx] = RingElem(self, coeffs=get_coeffs())
        return elems

    def binomial(self, bound: int, shape: int | tuple = None, *, seed=None) -> "RingElem | np.ndarray[RingElem]":
        if bound <= 0 or bound > self.q**0.5:  # only for performance reasons
            raise ValueError(f"bound must be positive and at most q^0.5, got {bound}")
        rng = SystemRandom() if seed is None else CryptoRandom(seed)
        get_coeffs = lambda: np.array(
            [rng.getrandbits(bound).bit_count() - rng.getrandbits(bound).bit_count() for _ in range(self.n)], 
            dtype=np.int64
        )
        if shape is None:
            return RingElem(self, coeffs=get_coeffs())
        elems = np.empty(shape, dtype=object)
        for idx in np.ndindex(shape):
            elems[idx] = RingElem(self, coeffs=get_coeffs())
        return elems
    
    def uniform(
            self, shape: int | tuple = None, *, lb: int = None, ub: int = None, seed=None, ntt=False
        ) -> "RingElem | np.ndarray[RingElem]":
        rng = SystemRandom() if seed is None else CryptoRandom(seed)
        lb = 0 if lb is None else lb
        ub = self.q - 1 if ub is None else ub
        if lb > ub:
            raise ValueError(f"lb must be less than or equal to ub, got lb={lb}, ub={ub}")
        randvec = lambda: np.array([rng.randint(lb, ub) for _ in range(self.n)], dtype=np.int64)
        get_elem = lambda: RingElem(self, coeffs=randvec()) if not ntt else RingElem(self, evals=self.ntt(randvec()))
        if shape is None:
            return get_elem()
        elems = np.empty(shape, dtype=object)
        for idx in np.ndindex(shape):
            elems[idx] = get_elem()
        return elems
    
    def sample_in_ball(self, weight: int, shape: int | tuple = None, *, seed=None) -> "RingElem | np.ndarray[RingElem]":
        if weight <= 0 or weight > self.n:
            raise ValueError(f"weight must be in [1, n], got {weight}")
        rng = SystemRandom() if seed is None else CryptoRandom(seed)
        
        def get_coeffs() -> np.ndarray:
            coeffs = np.zeros(self.n, dtype=np.int64)
            for i in rng.sample(range(self.n), weight):
                coeffs[i] = (-1)**rng.randint(0, 1)
            return coeffs
        
        if shape is None:
            return RingElem(self, coeffs=get_coeffs())
        elems = np.empty(shape, dtype=object)
        for idx in np.ndindex(shape):
            elems[idx] = RingElem(self, coeffs=get_coeffs())
        return elems

    def zero(self, shape: int | tuple = None) -> "RingElem | np.ndarray[RingElem]":
        zero = RingElem(
            self,
            coeffs=np.zeros(self.n, dtype=np.int64),
            evals=np.zeros(self.n, dtype=np.int64)
        )
        if shape is None:
            return zero
        elems = np.empty(shape, dtype=object)
        for idx in np.ndindex(shape):
            elems[idx] = zero.copy()
        return elems
    
    def one(self, shape: int | tuple = None) -> "RingElem | np.ndarray[RingElem]":
        one = RingElem(
            self,
            coeffs=np.array([1] + [0] * (self.n - 1), dtype=np.int64), 
            evals=np.ones(self.n, dtype=np.int64)
        )
        if shape is None:
            return one
        elems = np.empty(shape, dtype=object)
        for idx in np.ndindex(shape):
            elems[idx] = one.copy()
        return elems
    
    def eye(self, k: int) -> "np.ndarray[RingElem]":
        elems = np.empty((k, k), dtype=object)
        zero = self.zero()
        one = self.one()
        for i in range(k):
            for j in range(k):
                elems[i, j] = one.copy() if i == j else zero.copy()
        return elems
    
    def gen(self) -> "RingElem":
        return RingElem(self, coeffs=np.array([0] + [1] + [0] * (self.n - 2), dtype=np.int64))
    
    @functools.lru_cache(maxsize=None)
    def primitive_root(self) -> int:
        phi = self.q - 1
        for zeta in range(2, self.q):
            zeta = pow(zeta, phi // (2 * self.n), self.q)
            if pow(zeta, self.n, self.q) == self.q - 1:
                return zeta
        raise ValueError("no primitive root found")

    @functools.lru_cache(maxsize=None)
    def roots(self) -> np.ndarray:
        zeta = self.primitive_root()
        bitrev = lambda x: int(f"{x:0{self.n.bit_length() - 1}b}"[::-1], 2)
        return np.array([pow(zeta, bitrev(i), self.q) for i in range(self.n)], dtype=np.int64)

    def ntt(self, w: np.ndarray) -> np.ndarray:
        if isinstance(w, list):
            w = np.array(w, dtype=np.int64)
        if not isinstance(w, np.ndarray):
            raise TypeError(f"w must be of type np.ndarray, got {type(w).__name__}")
        if w.shape != (self.n,):
            raise ValueError(f"expected w of shape ({self.n},), got {w.shape}")
        q = self.q
        w = np.array(w, dtype=np.int64)
        zetas = self.roots()
        m, ell = 0, self.n // 2
        while ell > 0:
            for start in range(0, self.n, 2 * ell):
                z = zetas[m := m + 1]
                t = z * w[start + ell:start + 2 * ell] % q
                w[start + ell:start + 2 * ell] = (w[start:start + ell] - t) % q
                w[start:start + ell] = (w[start:start + ell] + t) % q
            ell >>= 1
        return w

    def intt(self, w: np.ndarray) -> np.ndarray:
        if isinstance(w, list):
            w = np.array(w, dtype=np.int64)
        if not isinstance(w, np.ndarray):
            raise TypeError(f"w must be of type np.ndarray, got {type(w).__name__}")
        if w.shape != (self.n,):
            raise ValueError(f"expected w of shape ({self.n},), got {w.shape}")
        q = self.q
        w = np.array(w, dtype=np.int64)
        zetas = self.roots()
        m, ell = self.n, 1
        while ell < self.n:
            for start in range(0, self.n, 2 * ell):
                z = -zetas[m := m - 1]
                t = w[start:start + ell].copy()
                w[start:start + ell] = (t + w[start + ell:start + 2 * ell]) % q
                w[start + ell:start + 2 * ell] = z * ((t - w[start + ell:start + 2 * ell]) % q) % q
            ell <<= 1
        return w * pow(self.n, -1, q) % q
    
    def from_bytes(self, data: bytes, *, ntt=False) -> "RingElem":
        if not isinstance(data, bytes):
            raise TypeError(f"data must be of type bytes, got {type(data).__name__}")
        if len(data) != self.n * 4:
            raise ValueError(f"expected {self.n * 4} bytes, got {len(data)} bytes")
        if ntt:
            evals = np.frombuffer(data, dtype=np.uint32).astype(np.int64) % self.q
            return RingElem(self, evals=evals)
        else:
            coeffs = np.frombuffer(data, dtype=np.uint32).astype(np.int64) % self.q
            return RingElem(self, coeffs=coeffs)


class RingElem:
    def __init__(self, ring: Ring, coeffs: np.ndarray = None, *, evals: np.ndarray = None) -> None:
        if coeffs is None and evals is None:
            raise ValueError("must specify either coeffs or evals")
        if not isinstance(ring, Ring):
            raise TypeError(f"ring must be of type Ring, got {type(ring).__name__}")
        if not (coeffs is None or isinstance(coeffs, np.ndarray)):
            raise TypeError(f"coeffs must be of type np.ndarray, got {type(coeffs).__name__}")
        if not (evals is None or isinstance(evals, np.ndarray)):
            raise TypeError(f"evals must be of type np.ndarray, got {type(evals).__name__}")
        self.ring = ring
        self.__coeffs = coeffs.astype(np.int64) if coeffs is not None else None
        self.__evals = evals.astype(np.int64) if evals is not None else None

    @property
    def coeffs(self) -> np.ndarray:
        if self.__coeffs is None:
            self.__coeffs = self.ring.intt(self.evals)
        return self.__coeffs
    
    @property
    def evals(self) -> np.ndarray:
        if self.__evals is None:
            self.__evals = self.ring.ntt(self.coeffs)
        return self.__evals
    
    @property
    def has_coeffs(self) -> bool:
        return self.__coeffs is not None
    
    @property
    def has_evals(self) -> bool:
        return self.__evals is not None

    def __add__(self, other) -> "RingElem | np.ndarray[RingElem]":
        if isinstance(other, np.ndarray):
            return other + self  # defer to ndarray addition
        if not isinstance(other, RingElem):
            other = self.ring(other)
        if self.ring != other.ring:
            raise ValueError("cannot add RingElem from different rings")
        if not (self.has_coeffs and other.has_coeffs or self.has_evals and other.has_evals):
            # defer to evals addition if the elements lack a common representation
            return RingElem(self.ring, evals=(self.evals + other.evals) % self.ring.q)
        return RingElem(
            self.ring,
            coeffs=(self.coeffs + other.coeffs) % self.ring.q if self.has_coeffs and other.has_coeffs else None,
            evals=(self.evals + other.evals) % self.ring.q if self.has_evals and other.has_evals else None
        )
    
    def __radd__(self, other) -> "RingElem | np.ndarray[RingElem]":
        return self + other
    
    def __sub__(self, other) -> "RingElem | np.ndarray[RingElem]":
        if isinstance(other, np.ndarray):
            return -other + self  # defer to ndarray addition
        if not isinstance(other, RingElem):
            other = self.ring(other)
        if self.ring != other.ring:
            raise ValueError("cannot subtract RingElem from different rings")
        if not (self.has_coeffs and other.has_coeffs or self.has_evals and other.has_evals):
            # defer to evals addition if the elements lack a common representation
            return RingElem(self.ring, evals=(self.evals - other.evals) % self.ring.q)
        return RingElem(
            self.ring,
            coeffs=(self.coeffs - other.coeffs) % self.ring.q if self.has_coeffs and other.has_coeffs else None,
            evals=(self.evals - other.evals) % self.ring.q if self.has_evals and other.has_evals else None
        )
    
    def __rsub__(self, other) -> "RingElem | np.ndarray[RingElem]":
        return self.ring(other) - self
    
    def __mul__(self, other) -> "RingElem | np.ndarray[RingElem]":
        if isinstance(other, np.ndarray):
            return other * self  # defer to ndarray multiplication
        if not isinstance(other, RingElem):
            other = self.ring(other)
        if self.ring != other.ring:
            raise ValueError("cannot multiply RingElem from different rings")
        return RingElem(self.ring, evals=(self.evals * other.evals) % self.ring.q)
    
    def __rmul__(self, other) -> "RingElem | np.ndarray[RingElem]":
        return self * other
    
    def inverse(self) -> "RingElem":
        if np.any(self.evals == 0):
            raise ZeroDivisionError("non-invertible element")
        inv_evals = np.array([pow(int(x), -1, self.ring.q) for x in self.evals], dtype=np.int64)
        return RingElem(self.ring, evals=inv_evals)
    
    def __truediv__(self, other) -> "RingElem | np.ndarray[RingElem]":
        if isinstance(other, np.ndarray):
            return (1 / other) * self  # defer to ndarray multiplication after inversion
        if not isinstance(other, RingElem):
            other = self.ring(other)
        if self.ring != other.ring:
            raise ValueError("cannot divide RingElem from different rings")
        if np.any(other.evals == 0):
            raise ZeroDivisionError("non-invertible element in division")
        inv_evals = np.array([pow(int(x), -1, self.ring.q) for x in other.evals], dtype=np.int64)
        return RingElem(self.ring, evals=(self.evals * inv_evals) % self.ring.q)

    __floordiv__ = __truediv__
    
    def __neg__(self) -> "RingElem":
        return RingElem(
            self.ring,
            coeffs=-self.coeffs if self.has_coeffs else None,
            evals=-self.evals if self.has_evals else None
        )
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, RingElem):
            try:
                other = self.ring(other)
            except Exception:
                return False
            return np.array_equal(self.evals, other.evals)
        return self.ring == other.ring and np.array_equal(self.evals, other.evals)
    
    def __ne__(self, other) -> bool:
        return not (self == other)
    
    def copy(self) -> "RingElem":
        return RingElem(
            self.ring,
            coeffs=self.coeffs.copy() if self.has_coeffs else None,
            evals=self.evals.copy() if self.has_evals else None
        )

    def __getitem__(self, idx: int) -> int:
        if not (0 <= idx < self.ring.n):
            raise IndexError(f"index out of range, got idx={idx}")
        return int(self.coeffs[idx] % self.ring.q)
    
    def centered_coeffs(self) -> np.ndarray:
        coeffs = np.array(self.coeffs % self.ring.q, dtype=np.int64)
        return np.where(coeffs <= self.ring.q // 2, coeffs, coeffs - self.ring.q)
    
    def __abs__(self) -> int:
        return int(np.max(np.abs(self.centered_coeffs())))
    
    def norm(self, p: int = 2) -> float:
        if p <= 0:
            raise ValueError(f"p must be positive, got {p}")
        coeffs = self.centered_coeffs().astype(np.float64)
        if p == np.inf:
            return float(np.max(np.abs(coeffs)))
        return float(np.sum(np.abs(coeffs)**p)**(1 / p))
    
    def power2round(self, d: int) -> tuple["RingElem", "RingElem"]:
        if d <= 0 or d >= self.ring.q.bit_length():
            raise ValueError(f"d must be in (0, log2(q)), got {d}")
        r = self.coeffs % self.ring.q
        r0 = r % (1 << d)
        r0 = np.where(r0 <= (1 << (d - 1)), r0, r0 - (1 << d))
        r1 = (r - r0) >> d
        return RingElem(self.ring, coeffs=r0), RingElem(self.ring, coeffs=r1)
    
    def decompose(self, gamma: int) -> tuple["RingElem", "RingElem"]:
        if gamma <= 0 or gamma >= self.ring.q // 2:
            raise ValueError(f"gamma must be in (0, q/2), got {gamma}")
        if (self.ring.q - 1) % (2 * gamma) != 0:
            raise ValueError(f"q - 1 must be divisible by 2*gamma, got q={self.ring.q}, gamma={gamma}")
        r = self.coeffs % self.ring.q
        r0 = r % (2 * gamma)
        r0 = np.where(r0 <= gamma, r0, r0 - 2 * gamma)
        mask = r - r0 == self.ring.q - 1
        r0 = np.where(mask, r0 - 1, r0)
        r1 = (r - r0) // (2 * gamma)
        r1 = np.where(mask, 0, r1)
        return RingElem(self.ring, coeffs=r0), RingElem(self.ring, coeffs=r1)
    
    def high_bits(self, gamma: int) -> "RingElem":
        _, r1 = self.decompose(gamma)
        return r1
    
    def low_bits(self, gamma: int) -> "RingElem":
        r0, _ = self.decompose(gamma)
        return r0

    def __poly_str(self) -> str:
        coeffs = reversed(self.centered_coeffs().astype(int))
        poly = ""
        for i, coeff in zip(reversed(range(self.ring.n)), coeffs):
            if coeff == 0:
                continue
            if poly:
                poly += " + " if coeff > 0 else " - "
                coeff = abs(coeff)
            if i == 0:
                poly += f"{coeff}"
                continue
            if abs(coeff) == 1:
                coeff = "" if poly and coeff > 0 else "-"
            if i == 1:
                poly += f"{coeff}x"
            else:
                poly += f"{coeff}x^{i}"
        return poly if poly else "0"

    def __repr__(self) -> str:
        return f"RingElem(ring={self.ring}, elem={self.__poly_str()})"
    
    def __str__(self) -> str:
        return self.__poly_str()
    
    def __hash__(self) -> int:
        return hash(str(self.ring).encode() + self.to_bytes(ntt=True))
    
    def __bytes__(self) -> bytes:
        return self.to_bytes(ntt=False)

    def to_bytes(self, *, ntt=False) -> bytes:
        if ntt:
            return (self.evals % self.ring.q).astype(np.uint32).tobytes()
        else:
            return (self.coeffs % self.ring.q).astype(np.uint32).tobytes()
    

if __name__ == "__main__":
    import time
    import galois

    q = 8380417  # Dilithium prime
    n = 256
    Rq = Ring(q=q, n=n)

    # test the ring element addition, subtraction, multiplication
    g1, g2 = Rq.uniform(), Rq.uniform()
    Zq = galois.GF(Rq.q, verify=False, compile="python-calculate")
    to_poly = lambda g: galois.Poly(g.coeffs.tolist(), field=Zq, order="asc")
    p1, p2 = to_poly(g1), to_poly(g2)
    mod = galois.Poly([1] + [0] * (n - 1) + [1], field=Zq, order="asc")  # x^n + 1  ->  x^n = -1
    assert p1 + p2 == to_poly(g1 + g2)
    assert p1 - p2 == to_poly(g1 - g2)
    # this is the slowest operation since it involves the modulus, ntt makes it so much faster
    tick = time.time()
    p3 = p1 * p2 % mod
    tock = time.time()
    print(f"poly mod mul time {tock - tick}")
    tick = time.time()
    g3 = g1 * g2  # this performs only the element-wise eval multiplication
    g3_poly = to_poly(g3)  # this performs the intt to recover the coefficients
    tock = time.time()
    print(f"elem ntt mul time {tock - tick}")
    assert p3 == g3_poly
