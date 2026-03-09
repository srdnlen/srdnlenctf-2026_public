from .abstract import WireLabel
from abc import ABC, abstractmethod
from collections import deque
from fastecdsa.curve import W25519
from fastecdsa.point import Point

__all__ = ['Channel', 'InMemoryChannel', 'StdIOChannel', 'PwnToolsChannel', 'point_to_bytes', 'bytes_to_point']


def point_to_bytes(point: Point) -> bytes:
    """ Converts a Point to its byte representation. """
    if not isinstance(point, Point):
        raise TypeError("point must be a Point instance")
    if point.curve != W25519:
        raise ValueError("only points on W25519 are supported")
    return (point.x | (point.y & 1) << 255).to_bytes(32, 'little')


def bytes_to_point(data: bytes) -> Point:
    """ Converts bytes to a Point on W25519. """
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) != 32:
        raise ValueError("data must be 32 bytes for W25519 point")
    x = int.from_bytes(data, 'little')
    bit, x = x >> 255, x & ((1 << 255) - 1)
    assert bit in {0, 1}
    # y^2 = x^3 + ax + b
    y2 = (pow(x, 3, W25519.p) + W25519.a * x + W25519.b) % W25519.p
    y = pow(y2, (W25519.p + 3) // 8, W25519.p)
    if pow(y, 2, W25519.p) == y2:
        pass
    elif pow(y, 2, W25519.p) == (-y2) % W25519.p:
        y = (y * pow(2, (W25519.p - 1) // 4, W25519.p)) % W25519.p
    else:
        raise ValueError("invalid point encoding")
    if x == 0 and bit == 1:
        raise ValueError("invalid point encoding")
    if (y & 1) != bit:
        y = W25519.p - y
    return Point(x, y, W25519)


class Channel(ABC):
    """ Abstract communication channel for sending and receiving wire labels and points. """

    @abstractmethod
    def send_wire(self, wire: WireLabel):
        """ Sends a wire label through the channel. """
        pass

    def send_wires(self, wires: list[WireLabel]):
        """ Sends multiple wire labels through the channel. """
        for wire in wires:
            self.send_wire(wire)

    @abstractmethod
    def send_point(self, point: Point):
        """ Sends a point through the channel. """
        pass
    
    @abstractmethod
    def read_wire(self) -> WireLabel:
        """ Reads a wire label from the channel. """
        pass

    def read_wires(self, n: int) -> list[WireLabel]:
        """ Reads multiple wire labels from the channel. """
        return [self.read_wire() for _ in range(n)]

    @abstractmethod
    def read_point(self) -> Point:
        """ Reads a point from the channel. """
        pass


class InMemoryChannel(Channel):
    def __init__(self):
        self.wire_buffer = deque()
        self.point_buffer = deque()
    
    def send_wire(self, wire: WireLabel):
        self.wire_buffer.append(wire)
    
    def send_point(self, point: Point):
        self.point_buffer.append(point)
    
    def read_wire(self) -> WireLabel:
        if not self.wire_buffer:
            raise RuntimeError("No data to receive")
        return self.wire_buffer.popleft()
    
    def read_point(self) -> Point:
        if not self.point_buffer:
            raise RuntimeError("No data to receive")
        return self.point_buffer.popleft()


class StdIOChannel(Channel):
    def send_wire(self, wire: WireLabel):
        print(f"{wire:032x}")
    
    def send_point(self, point: Point):
        data = point_to_bytes(point)
        print(data.hex())
    
    def read_wire(self) -> WireLabel:
        line = input().strip()
        return int(line, 16)
    
    def read_point(self) -> Point:
        line = input().strip()
        data = bytes.fromhex(line)
        return bytes_to_point(data)


class PwnToolsChannel(Channel):
    def __init__(self, io):
        from pwn import process
        self.io: process = io

    def send_wire(self, wire: WireLabel):
        data = wire.to_bytes(16, 'big')
        self.io.sendline(data.hex().encode())

    def send_point(self, point: Point):
        data = point_to_bytes(point)
        self.io.sendline(data.hex().encode())

    def read_wire(self) -> WireLabel:
        line = self.io.recvline(False)
        return int(line, 16)

    def read_point(self) -> Point:
        line = self.io.recvline(False)
        data = bytes.fromhex(line.decode())
        return bytes_to_point(data)
