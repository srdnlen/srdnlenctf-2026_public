from ts import TSParam, TS
import os, json, signal

param = TSParam(N=16, T=8)
target = b"give me the flag"

trusted = TS(param)
vk, sk = trusted.keygen(os.urandom(32))
trusted.receive_vk(vk)

you = 0
signer = {i: TS(param) for i in range(1, param.N)}
print(f'Your secret key and verification key: {json.dumps({"vk": vk, "sk": sk[you]})}')
for i in range(1, param.N):
    signer[i].receive_vk(vk)
    signer[i].receive_ski(i, sk[i])
del sk  # forget secret keys

signal.alarm(8 * 60)  # 8 minutes

print(f"""
Welcome to the threshold signature server!
You are signer #{you}.
You can request signatures from other signers to collaboratively sign messages.
1) Add preprocessing data
2) Request a threshold signature on a message
3) Get the flag (only if you have a valid signature on "{target.decode()}")
*) Exit
""")
while True:
    choice = input("Your choice: ").strip()
    
    if choice == "1":
        if len(signer[1].commitment_cache[you]) >= 8:
            print("You have already provided enough preprocessing data!")
            continue
        your_w = json.loads(input("Get your preprocessing data: "))
        for i in range(1, param.N):
            signer[i].receive_commitment(you, your_w)
        for i in range(1, param.N):
            if len(signer[i].masking_cache) >= 8:
                continue  # limit preprocessing data to avoid memory exhaustion
            wi = signer[i].preprocessing()
            print(f"Preprocessing data from signer #{i}: {json.dumps(wi)}")
            for j in range(1, param.N):
                if j != i:
                    signer[j].receive_commitment(i, wi)
    
    elif choice == "2":
        msg = bytes.fromhex(input("Message to sign (hex): ").strip())
        if msg == target:
            print("You cannot request a signature on this message!")
            continue
        S = list(map(int, input(f"Select {param.T} signers from [1-{param.N}]: ").strip().split()))
        S.append(you)
        S = sorted(set(S))
        if len(S) != param.T:
            print(f"You must select exactly {param.T} distinct signers!")
            continue
        for i in S:
            if i != you:
                sig = signer[i].sign(S, msg)
                print(f"Partial signature from signer #{i}: {json.dumps(sig)}")
        for i in range(1, param.N):
            if i in S:
                continue
            for j in S:
                signer[i].commitment_cache[j].pop(0)
    
    elif choice == "3":
        sig = json.loads(input(f"Signature on '{target.decode()}': ").strip())
        if trusted.verify(target, sig):
            print(f"Here is your flag: {os.getenv('FLAG', 'srdnlen{this_is_a_fake_flag}')}")
        else:
            print("Invalid signature!")
        break
    
    else:
        print("Goodbye!")
        break
