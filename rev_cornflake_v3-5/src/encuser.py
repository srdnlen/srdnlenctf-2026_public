import binascii

def rc4(data, key):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    res = bytearray()
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        res.append(byte ^ S[(S[i] + S[j]) % 256])
    return res

key = b"s3cr3t_k3y_v1"
user = b"super_powerful_admin"
print(binascii.hexlify(rc4(user, key)).decode())

encrypted_data = binascii.unhexlify("46f5289437bc009c17817e997ae82bfbd065545d")


def rc4_crypt(data, key):
    """
    Standard RC4 implementation.
    """
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]

    i = 0
    j = 0
    res = bytearray()
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        res.append(byte ^ k)
    
    return res

RC4_KEY = b"s3cr3t_k3y_v1" 
# 2. Decrypt RC4
decrypted_username = rc4_crypt(encrypted_data, RC4_KEY)

print(f"    Decrypted Identity: {decrypted_username}")
# 3. Verify Identity
