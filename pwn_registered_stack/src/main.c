#include <stdio.h>
#include <capstone/capstone.h>
#include <stdbool.h>
#include <sys/mman.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

#define MMAP_SIZE 0x1000
#define BYTES_LEN 0x100


void panic(const char* err_msg) {
	fputs(err_msg, stderr);
	exit(EXIT_FAILURE);
}


bool validate_code(unsigned char *code, size_t code_size) {
	csh handle;
	cs_insn *insn;
	size_t count;
	bool result = true;
	size_t bytes_covered = 0;

	// Initialize Capstone disassembler
	if (cs_open(CS_ARCH_X86, CS_MODE_64, &handle) != CS_ERR_OK) {
		panic("Failed to initialize Capstone");
	}

	// Enable detail mode to get operand information
	cs_option(handle, CS_OPT_DETAIL, CS_OPT_ON);

	// Disassemble the code
	count = cs_disasm(handle, code, code_size, 0x0, 0, &insn);
	if (count <= 0) {
		panic("Failed to disassemble code");
	}

	for (size_t i = 0; i < count; i++) {
		cs_detail *detail = insn[i].detail;

		// Track how many bytes we've successfully disassembled
		bytes_covered += insn[i].size;

		// Check if instruction is PUSH or POP
		if (insn[i].id != X86_INS_PUSH && insn[i].id != X86_INS_POP) {
			printf("Error at instruction %zu: '%s %s' is not PUSH or POP\n", i, insn[i].mnemonic, insn[i].op_str);
			result = false;
			continue;
		}

		if (detail) {
			cs_x86 *x86 = &detail->x86;

			// Check if instruction has operands
			if (x86->op_count == 0) {
				printf("Error at instruction %zu: '%s' has no operands\n", i, insn[i].mnemonic);
				result = false;
				continue;
			}

			// Check if all operands are registers
			for (int j = 0; j < x86->op_count; j++) {
				if (x86->operands[j].type != X86_OP_REG) {
					printf("Error at instruction %zu: '%s %s' uses non-register operand\n", i, insn[i].mnemonic, insn[i].op_str);
					result = false;
					break;
				}
			}
		}
	}

	// Ensure all bytes were successfully disassembled
	if (bytes_covered != code_size) {
		printf("Only %zu/%zu bytes were disassembled\n", bytes_covered, code_size);
		result = false;
	}

	// Cleanup
	cs_free(insn, count);
	cs_close(&handle);
	return result;
}


// Convert hex string to bytes
size_t hex_to_bytes(const char *hex_str, unsigned char *output, size_t max_len) {
	size_t len = strlen(hex_str);
	size_t byte_count = 0;

	for (size_t i = 0; i + 1 < len && byte_count < max_len; i+=2) {

		// Break on non-hex characters
		if (!isxdigit(hex_str[i]) || !isxdigit(hex_str[i + 1])) {
			break;
		}

		// Convert two hex digits to one byte
		char hex_byte[3] = {hex_str[i], hex_str[i + 1], '\0'};
		output[byte_count++] = (unsigned char)strtol(hex_byte, NULL, 16);
	}

	return byte_count;
}


int main(int argc, char** argv) {

	// Allocate code space
	unsigned char* code = mmap(NULL, MMAP_SIZE, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
	if (code == MAP_FAILED) {
		panic("Failed mmap");
	}

	// Allocate buffer space
	char* buffer = malloc(2*BYTES_LEN);
	if (buffer == NULL) {
		panic("Failed malloc");
	}

	// Read hex code
	printf("Write your code > ");
	fgets(buffer, 2*BYTES_LEN, stdin);

	//Convert hex to bytes
	size_t code_size = hex_to_bytes(buffer, code, BYTES_LEN);
	free(buffer);
	buffer = NULL;

	// Validate code
	if (!validate_code(code, code_size)) {
		panic("Invalid code");
	}

	// Execute code
	__asm__ volatile (

		// Set RSP to point to the shellcode
		"mov %0, %%rax\n"
		"mov %%rax, %%rsp\n"

		// Clear all general purpose registers
		"xor %%rax, %%rax\n"
		"xor %%rbx, %%rbx\n"
		"xor %%rcx, %%rcx\n"
		"xor %%rdx, %%rdx\n"
		"xor %%rsi, %%rsi\n"
		"xor %%rdi, %%rdi\n"
		"xor %%r8, %%r8\n"
		"xor %%r9, %%r9\n"
		"xor %%r10, %%r10\n"
		"xor %%r11, %%r11\n"
		"xor %%r12, %%r12\n"
		"xor %%r13, %%r13\n"
		"xor %%r14, %%r14\n"
		"xor %%r15, %%r15\n"
		"xor %%rbp, %%rbp\n"

		// Clear FS and GS segment selectors (will zero fs_base and gs_base)
		"mov %%ax, %%fs\n"
		"mov %%ax, %%gs\n"

		// Jump to shellcode
		"jmp *%%rsp\n"
		:
		: "r"(code)
		: "memory"
	);

	return 0;
}


__attribute__((constructor))
void init() {
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
}
