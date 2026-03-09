#include <stdlib.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>

#define BUFFER_SIZE 64


void read_stdin(char* buf, u_int8_t num_char) {
	for (u_int8_t i = 0; i <= num_char; ++i ) {
		if ( read(STDIN_FILENO, &buf[i], 1uLL) != 1 || buf[i] == '\n' ) {
			buf[i] = 0;
			break;
		}
	}
}


void echo() {

	struct Stack {
		char buffer[BUFFER_SIZE];
		u_int8_t size;
	} stack;

	memset(stack.buffer, 0, BUFFER_SIZE);
	stack.size = BUFFER_SIZE;

	while (true) {
		printf("echo ");
		read_stdin(stack.buffer, stack.size);
		if (strlen(stack.buffer) == 0) {
			break;
		}
		printf("%s\n", stack.buffer);
	}
}


int main(int argc, char** argv) {
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
	echo();
	return 0;
}
