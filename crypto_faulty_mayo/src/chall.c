// SPDX-License-Identifier: Apache-2.0

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <randombytes.h>
#include <mayo.h>
#include <stdalign.h>

static void print_hex(const unsigned char *hex, int len) {
    for (int i = 0; i < len;  ++i) {
        printf("%02x", hex[i]);
    }
    printf("\n");
}

static int gen_key(const mayo_params_t *p) {
    unsigned char _pk[CPK_BYTES_MAX + 1] = {0};  
    unsigned char _sk[CSK_BYTES_MAX + 1] = {0};

    // Enforce unaligned memory addresses
    unsigned char *pk  = (unsigned char *) ((uintptr_t)_pk | (uintptr_t)1);
    unsigned char *sk  = (unsigned char *) ((uintptr_t)_sk | (uintptr_t)1);

    unsigned char seed[48] = { 0 };
    randombytes_init(seed, NULL, 256);

    int res = mayo_keypair(p, pk, sk);
    if (res != MAYO_OK) {
        res = -1;
        printf("keygen failed!\n");
        goto err;
    }

    FILE* pk_fp = fopen("pk.bin", "w");
    FILE* sk_fp = fopen("sk.bin", "w");

    fwrite(pk, sizeof(unsigned char), PARAM_cpk_bytes(p), pk_fp);
    fwrite(sk, sizeof(unsigned char), PARAM_csk_bytes(p), sk_fp);

    fclose(pk_fp);
    fclose(sk_fp);

    printf("key generated!\n");

err:
    return res;
}

static int get_signature(const mayo_params_t *p) {
    unsigned char _pk[CPK_BYTES_MAX + 1] = {0};  
    unsigned char _sk[CSK_BYTES_MAX + 1] = {0};
    unsigned char _sig[SIG_BYTES_MAX + 32 + 1] = {0};
    unsigned char _msg[32+1] = { 0 };

    // Enforce unaligned memory addresses
    unsigned char *pk  = (unsigned char *) ((uintptr_t)_pk | (uintptr_t)1);
    unsigned char *sk  = (unsigned char *) ((uintptr_t)_sk | (uintptr_t)1);
    unsigned char *sig = (unsigned char *) ((uintptr_t)_sig | (uintptr_t)1);
    unsigned char *msg = (unsigned char *) ((uintptr_t)_msg | (uintptr_t)1);

    unsigned char seed[48] = { 0 };
    randombytes_init(seed, NULL, 256);

    size_t msglen = 32;
    randombytes(msg, msglen);

    FILE* pk_fp = fopen("pk.bin", "r");
    FILE* sk_fp = fopen("sk.bin", "r");

    int res = MAYO_OK;
    if (pk_fp == NULL || sk_fp == NULL) {
        res = -1;
    }
    else if (fread(pk, sizeof(unsigned char), PARAM_cpk_bytes(p), pk_fp) != (size_t)PARAM_cpk_bytes(p)) {
        res = -1;
    }
    else if (fread(sk, sizeof(unsigned char), PARAM_csk_bytes(p), sk_fp) != (size_t)PARAM_csk_bytes(p)) {
        res = -1;
    }

    if (pk_fp != NULL) {
        fclose(pk_fp);
    }
    if (sk_fp != NULL) {
        fclose(sk_fp);
    }

    if (res != MAYO_OK) {
        printf("key loading failed!\n");
        goto err;
    }

    size_t smlen = PARAM_sig_bytes(p) + 32;

    res = mayo_sign(p, sig, &smlen, msg, 32, sk);
    if (res != MAYO_OK) {
        res = -1;
        printf("sign failed!\n");
        goto err;
    }

    printf("pk: ");
    print_hex(pk, PARAM_cpk_bytes(p));
    printf("sm: ");
    print_hex(sig, smlen);

    res = mayo_open(p, msg, &msglen, sig, smlen, pk);
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
    int res = MAYO_OK;
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
        return MAYO_ERR;
    }

    if (argc > 2 && !strcmp(argv[2], "GENKEY")) {
        res = gen_key(p);
    }
    else {
        res = get_signature(p);
    }

    return res;
}
