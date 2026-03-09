// SPDX-License-Identifier: Apache-2.0

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <randombytes.h>
#include <mayo.h>
#include <stdalign.h>

static int is_hex_char(char c) {
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
}

static int bytes_from_hex(unsigned char* bytes, size_t len, char* hex) {
    if (strlen(hex) != 2*len) {
        return MAYO_ERR;
    }

    for (int i = len-1; i >= 0; i--) {
        if (!is_hex_char(hex[2*i]) || !is_hex_char(hex[2*i+1])) {
            return MAYO_ERR;
        }
        bytes[i] = strtol(&hex[2*i], NULL, 16);
        hex[2*i] = 0;
    }

    return MAYO_OK;
}

static int verify_signature(const mayo_params_t *p, char* msg, char* sig_hex) {
    unsigned char _pk[CPK_BYTES_MAX + 1] = {0};  
    unsigned char _sig[SIG_BYTES_MAX + 32 + 1] = {0};

    // Enforce unaligned memory addresses
    unsigned char *pk  = (unsigned char *) ((uintptr_t)_pk | (uintptr_t)1);
    unsigned char *sig = (unsigned char *) ((uintptr_t)_sig | (uintptr_t)1);

    unsigned char seed[48] = { 0 };
    randombytes_init(seed, NULL, 256);

    size_t msglen = 32;

    FILE* pk_fp = fopen("pk.bin", "r");

    int res = MAYO_OK;
    if (pk_fp == NULL) {
        res = -1;
    }
    else if (fread(pk, sizeof(unsigned char), PARAM_cpk_bytes(p), pk_fp) != (size_t)PARAM_cpk_bytes(p)) {
        res = -1;
    }

    if (pk_fp != NULL) {
        fclose(pk_fp);
    }

    if (res != MAYO_OK) {
        printf("key loading failed!\n");
        goto err;
    }

    size_t smlen = PARAM_sig_bytes(p) + 32;

    res = bytes_from_hex(sig, smlen, sig_hex);
    if (res != MAYO_OK) {
        res = -1;
        printf("verify failed at decoding stage!\n");
        goto err;
    }

    if (memcmp(sig + PARAM_sig_bytes(p), msg, msglen)) {
        res = -1;
        printf("verify failed, signature has different message!\n");
        goto err;
    }

    res = mayo_open(p, (unsigned char*)msg, &msglen, sig, smlen, pk);
    if (res != MAYO_OK) {
        res = -1;
        printf("verify failed!\n");
        goto err;
    }

    printf("verify success!\n");

err:
    return res;
}

int main(int argc, char *argv[]) {
    int res = MAYO_ERR;
    const mayo_params_t* p;

    if (!strcmp(argv[1], "MAYO-1")) {
        p = &MAYO_1;
    } else if (!strcmp(argv[1], "MAYO-2")) {
        p = &MAYO_2;
    } else if (!strcmp(argv[1], "MAYO-3")) {
        p = &MAYO_3;
    } else if (!strcmp(argv[1], "MAYO-5")) {
        p = &MAYO_5;
    } else {
        printf("unknown parameter set\n");
        return res;
    }

    if (argc > 3) {
        res = verify_signature(p, argv[2], argv[3]);
    }

    return res;
}
