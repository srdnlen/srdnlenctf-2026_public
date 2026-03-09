from random import Random
import xoflib

BPF = 53        # Number of bits in a float
RECIP_BPF = 2 ** -BPF


class CryptoRandom(Random):
    def random(self) -> float:
        """Get the next random number in the range 0.0 <= X < 1.0."""
        return (int.from_bytes(self.xof.read(7)) >> 3) * RECIP_BPF

    def getrandbits(self, k: int) -> int:
        """getrandbits(k) -> x.  Generates an int with k random bits."""
        if k < 0:
            raise ValueError('number of bits must be non-negative')
        numbytes = (k + 7) // 8                       # bits / 8 and rounded up
        x = int.from_bytes(self.xof.read(numbytes))
        return x >> (numbytes * 8 - k)                # trim excess bits

    def randbytes(self, n: int) -> bytes:
        """Generate n random bytes."""
        return self.xof.read(n)

    def seed(self, a=None, version=2, xof=xoflib.blake3_xof):
        """ Initialize internal state from hash of a. """
        if a is None:
            import os
            a = os.urandom(64)
        if isinstance(a, (str, bytes, bytearray)):
            if isinstance(a, str):
                a = a.encode()
            import hashlib
            a = int.from_bytes(a + hashlib.sha512(a).digest())
        elif not isinstance(a, (type(None), int, float, str, bytes, bytearray)):
            raise TypeError('The only supported seed types are: None,\n'
                            'int, float, str, bytes, and bytearray.')

        self.xof = xof(hex(a).encode())
        self.gauss_next = None
    
    def _notimplemented(self, *args, **kwds):
        "Method should not be called for a system random number generator."
        raise NotImplementedError('System entropy source does not have state.')
    getstate = setstate = _notimplemented
