#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include <stdbool.h>

#define MAX_QUERIES (1 << 16)
#define NROUNDS 4
#define IV 0x7372646e6c656e21ULL
#define RROT(x, n) (((x) >> (n)) | ((x) << (64 - (n))))

const uint64_t RC[] = {
    0x0000000000000073ULL, 0x0000000000000072ULL, 0x0000000000000064ULL, 0x000000000000006eULL, 
    0x000000000000006cULL, 0x0000000000000065ULL, 0x000000000000006eULL, 0x0000000000000032ULL, 
    0x0000000000000030ULL, 0x0000000000000032ULL, 0x0000000000000036ULL, 0x0000000000000021ULL
};

static inline void permutation(uint64_t x[5], const size_t r) {
    // Constant-Addition Layer
    x[2] ^= RC[r];
    // Substitution Layer
    x[0] ^= x[4];
    x[2] ^= x[1];
    x[4] ^= x[3];
    uint64_t t[5];
    for (size_t i = 0; i < 5; i++) {
        t[i] = x[i] ^ ((~x[(i + 1) % 5]) & x[(i + 2) % 5]);
    }
    for (size_t i = 0; i < 5; i++) {
        x[i] = t[i];
    }
    x[1] ^= x[0];
    x[3] ^= x[2];
    x[0] ^= x[4];
    x[2] = ~x[2];
    // Linear Diffusion Layer
    x[0] ^= RROT(x[0], 19) ^ RROT(x[0], 28);
    x[1] ^= RROT(x[1], 61) ^ RROT(x[1], 39);
    x[2] ^= RROT(x[2], 1) ^ RROT(x[2], 6);
    x[3] ^= RROT(x[3], 10) ^ RROT(x[3], 17);
    x[4] ^= RROT(x[4], 7) ^ RROT(x[4], 41);
}

void ascon(const uint64_t key[2], const uint64_t nonce[2], uint64_t out[2]) {
    uint64_t state[5] = {IV, key[0], key[1], nonce[0], nonce[1]};
    for (size_t r = 0; r < NROUNDS; r++) {
        permutation(state, r);
    }
    out[0] = state[0];
    out[1] = state[1];
}

// From Dilithium reference implementation
void randombytes(uint8_t *out, size_t outlen) {
    static int fd = -1;
    ssize_t ret;

    while(fd == -1) {
        fd = open("/dev/urandom", O_RDONLY);
        if(fd == -1 && errno == EINTR)
            continue;
        else if(fd == -1)
            abort();
    }

    while(outlen > 0) {
        ret = read(fd, out, outlen);
        if(ret == -1 && errno == EINTR)
            continue;
        else if(ret == -1)
            abort();

        out += ret;
        outlen -= ret;
    }
}

int main() {
    uint64_t key[2];
    uint64_t nonce[2];
    uint64_t diff[2];
    uint64_t out[2];
    
    randombytes((uint8_t *)key, 16);
    
    for (size_t i = 0; i < MAX_QUERIES; i++) {
        int res = scanf("%16llx%16llx", &diff[0], &diff[1]);
        if (res != 2) abort();
        if (diff[0] == 0 && diff[1] == 0)
            break;
        
        randombytes((uint8_t *)nonce, 16);
        printf("%016llx%016llx\n", nonce[0], nonce[1]);
        ascon(key, nonce, out);
        printf("%016llx%016llx\n", out[0], out[1]);
        nonce[0] ^= diff[0];
        nonce[1] ^= diff[1];
        ascon(key, nonce, out);
        printf("%016llx%016llx\n", out[0], out[1]);
    }

    uint64_t guess[2];
    int res = scanf("%16llx%16llx", &guess[0], &guess[1]);
    if (res != 2) abort();
    if (guess[0] != key[0] || guess[1] != key[1]) {
        printf("Wrong key!\n");
        return 1;
    }
    printf("Correct key!\n");

    char *flag = getenv("FLAG");
    if (flag != NULL) {
        printf("%s\n", flag);
    } else {
        printf("srdnlen{this_is_a_fake_flag}\n");
    }
    return 0;
}

__attribute__((constructor))
void init() {
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
}
