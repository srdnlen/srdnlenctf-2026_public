from sage.all import ZZ, GF, vector, Matrix
import ast
import tqdm
from functools import reduce
from pwn import connect, process, context

context.log_level = "CRITICAL"

MAYO_SCHEME = "MAYO-2"
n = 81
m = 64
o = 17
k = 4
q = 16

distance1 = 24
distance2 = 22
distance3 = 27
with open("chall", "rb") as f:
    chall_binary = f.read()
assert chall_binary.count(bytes.fromhex("0f849a050000")) == 1
base = chall_binary.index(bytes.fromhex("0f849a050000"))+23

pk_ok = False
Fq = GF(q, "z")
O = Matrix(ZZ, m, o)

for i in tqdm.trange(m):
    a = vector(Fq, o)
    X = Matrix(Fq, o, o)
    t = 0
    while t < o:
        io = connect("mayo.challs.srdnlen.it", 1340)

        io.sendline(b"1")
        io.sendline(str(base+(distance1 if i > 0 else 0)+max(min(i, m-2)-1, 0)*distance2+(distance3 if i == m-1 else 0)).encode())
        io.sendline(b"0")
        io.sendline(b"7")

        io.recvuntil(b"with code: ")
        code = int(io.recvline(False).decode())

        io.recvuntil(b"output: ")
        output = ast.literal_eval(io.recvline(False).decode()).decode()

        io.close()

        if not pk_ok:
            pk_ok = True
            pk = output.split("pk: ")[1].split("\n")[0]
            with open("pk.bin", "wb") as f:
                f.write(bytes.fromhex(pk))
        sm = output.split("sm: ")[1].split("\n")[0]

        dec_s = bytes.fromhex("".join(["0"+sm[j+1]+"0"+sm[j] for j in range(0, k*n, 2)]))

        for j in range(0, k*n, n):
            x = vector(Fq, [Fq.from_integer(el) for el in dec_s[j+m:j+n]])
            prev_rank = X.rank()
            X[:, t] = x
            if X.rank() == prev_rank:
                continue
            alpha = dec_s[j+i]
            a[t] = Fq.from_integer(alpha)
            t += 1
            if t == o:
                break

    inv_X = X.inverse()
    tmp = a*inv_X
    O[i, :] = vector(ZZ, [el.to_integer() for el in tmp])

O_bytes = bytes(reduce(lambda x,y: x+y, [list(map(int, sub)) for sub in O]))

with open("O.bin", "wb") as f:
    f.write(O_bytes)

io = connect("mayo.challs.srdnlen.it", 1340)

io.sendline(b"2")

io.recvuntil(b"for the message \"")
msg = io.recvuntil(b"\"", drop=True)

solve = process(["./sign", MAYO_SCHEME, msg])

res = solve.recvline(False).decode()

if res != "signature was successful!":
    print(res)
    quit()

sig = solve.recvline(False).decode()

solve.close()

io.sendline(sig.encode())

io.interactive()
