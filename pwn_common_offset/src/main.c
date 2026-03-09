#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <sys/types.h>

#define NUM_BUFFERS 4
#define LEN_BUFFER 0x20
#define WRITE_LIMIT 2

char buffers[NUM_BUFFERS][LEN_BUFFER];
bool exit_flag = false;

struct Files {
    char* buffers[NUM_BUFFERS];
    u_int8_t* index;
    u_int8_t* offset;
};


void panic(char* error_msg) {
    puts(error_msg);
    exit(EXIT_FAILURE);
}

void read_stdin(char* buffer, size_t len) {
    if (fgets(buffer, len, stdin) != buffer) {
        panic("Error reading stdin");
    }
}

u_int8_t get_number() {
    char buffer[16];
    char* endptr;

    read_stdin(buffer, sizeof(buffer));

    unsigned long val = strtoul(buffer, &endptr, 10);
    if (endptr == buffer || (*endptr != '\n' && *endptr != '\0')) {
        panic("Invalid number");
    }
    return (u_int8_t)val;
}


void write_chars(struct Files* files) {
    printf("Write on the file:\n> ");
    read_stdin(&(files->buffers[*(files->index)][*(files->offset)]), LEN_BUFFER-(*(files->offset)));
}

void change_files(char* nickname) {
    struct {
        u_int8_t counter;
        struct Files files;
        u_int8_t offset;
        u_int8_t index;
    } stack;

    // Init
    for (stack.counter = 0; stack.counter < NUM_BUFFERS; stack.counter++) {
        stack.files.buffers[stack.counter] = buffers[stack.counter];
    }
    stack.files.index = &(stack.index);
    stack.files.offset = &(stack.offset);
    stack.offset = 0;
    stack.index = 0;

    for (stack.counter = WRITE_LIMIT; stack.counter > 0; stack.counter--) {
        printf("You can still write on %hhu files!\n", stack.counter);
        
        // Choose index
        printf("Choose the index:\n> ");
        stack.index = get_number();
        if (stack.index >= NUM_BUFFERS) {
            panic("Invalid index");
        }
        
        // Increase offset
        printf("Increase the offset:\n> ");
        *(u_int16_t*)(&(stack.offset)) += get_number(); // VULNERABLE
        if (stack.offset >= LEN_BUFFER) {
            panic("Invalid offset");
        }

        // Write on file
        write_chars(&(stack.files));
    }

    // No return to this function
    if (exit_flag) {
        panic("This is a one-time function");
    }
    exit_flag = true;

    printf("Goodbye, %s!\n", nickname);
    asm("mov %0, %%rdi" : : "r"(nickname));
}

int main(int argc, char** argv) {
    char nickname[8] = {0};

    // Get name
    printf("Put your name:\n> ");
    read_stdin(nickname, sizeof(nickname));

    // Validate name
    for (size_t i = strspn(nickname, "0123456789abcdefghijklmnopqrstuvwxyz"); i < sizeof(nickname); i++) {
        nickname[i] = '\0';
    }

    change_files(nickname);
    return 0;
}

__attribute__((constructor))
void init() {
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
}
