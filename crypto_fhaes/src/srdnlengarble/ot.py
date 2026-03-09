from .garble import WireLabel, point_to_bytes, Channel
from fastecdsa.curve import W25519
from fastecdsa.point import Point
import secrets, hashlib

__all__ = ['Sender', 'Receiver']


def hash_point(point: Point, tweak: bytes) -> WireLabel:
    """ Hashes a point with a tweak to produce a wire label. """
    if not isinstance(point, Point):
        raise TypeError("point must be a Point instance")
    if not isinstance(tweak, bytes):
        raise TypeError("tweak must be bytes")
    data = point_to_bytes(point) + tweak
    digest = hashlib.shake_128(data).digest(16)
    return WireLabel.from_bytes(digest, 'big')


class Sender:
    def __init__(self, channel: Channel):
        """ Initializes the Sender with a communication channel. """
        if not isinstance(channel, Channel):
            raise TypeError("channel must be an instance of Channel")
        self.channel = channel
        self.x = secrets.randbelow(W25519.q - 1) + 1
        self.P = self.x * W25519.G
        self.counter = 0
        # Sender ---> Receiver: P = x * G
        channel.send_point(self.P)

    def send(self, wires: list[tuple[WireLabel, WireLabel]]):
        """ Sends in OT the wire labels for the evaluator to choose from. """
        if not isinstance(wires, list):
            raise TypeError("wires must be a list")
        if not all(isinstance(pair, tuple) and len(pair) == 2 for pair in wires):
            raise TypeError("each wire must be a tuple of two WireLabels")
        Q = self.x * self.P
        for zero, one in wires:
            # Receiver ---> Sender: R_i = r_i * G + b_i * P
            R = self.channel.read_point()
            S0 = self.x * R
            S1 = S0 - Q
            tweak = self.counter.to_bytes(16, 'little')
            k0 = hash_point(S0, tweak) ^ zero
            k1 = hash_point(S1, tweak) ^ one
            # Sender ---> Receiver: H(R_i * x), H((R_i - P) * x)
            self.channel.send_wire(k0)
            self.channel.send_wire(k1)
            self.counter += 1


class Receiver:
    def __init__(self, channel: Channel):
        """ Initializes the Receiver with a communication channel. """
        if not isinstance(channel, Channel):
            raise TypeError("channel must be an instance of Channel")
        self.channel = channel
        # Sender ---> Receiver: P = x * G
        self.P = channel.read_point()
        self.counter = 0

    def receive(self, choices: list[bool | int]) -> list[WireLabel]:
        """ Receives in OT the chosen wire labels based on the choice bits. """
        if not isinstance(choices, list):
            raise TypeError("choices must be a list")
        if not all(isinstance(bit, (bool, int)) for bit in choices):
            raise TypeError("each choice must be a boolean or integer")
        ks = []
        for bit in choices:
            r = secrets.randbelow(W25519.q - 1) + 1
            R = r * W25519.G + self.P if bit else r * W25519.G
            # Receiver ---> Sender: R_i = r_i * G + b_i * P
            self.channel.send_point(R)
            k = hash_point(r * self.P, self.counter.to_bytes(16, 'little'))
            ks.append(k)
            self.counter += 1
        wires = []
        for k, bit in zip(ks, choices):
            # Sender ---> Receiver: H(R_i * x), H((R_i - P) * x)
            c0 = self.channel.read_wire()
            c1 = self.channel.read_wire()
            wire = c1 ^ k if bit else c0 ^ k
            wires.append(wire)
        return wires
