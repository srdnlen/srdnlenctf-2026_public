#!/usr/bin/env python3

import json

from pwn import *
from solve import download_unicode_emoji_pool, build_solver_cache, solve_captcha


if args.DEBUG:
    context.log_level = "DEBUG"


HOST = os.getenv("HOST", "emoji.challs.srdnlen.it")
PORT = int(os.getenv("PORT", 1717))

UNICODE_URL = "https://unicode.org/Public/emoji/latest/emoji-test.txt"
FONT_PATH = "AppleColorEmoji-160px.ttf"

EMOJI_POOL_PATH = "emoji_pool.json"
EMOJI_POOL: list[dict[str, str]] = []

ROUND = 100

if not os.path.exists(EMOJI_POOL_PATH):
    print("[*] Downloading emoji pool...")
    EMOJI_POOL = download_unicode_emoji_pool(UNICODE_URL, EMOJI_POOL_PATH)

else:
    print("[*] Loading emoji pool from file...")
    with open(EMOJI_POOL_PATH, "r", encoding="utf-8") as f:
        EMOJI_POOL = json.load(f)

print(f"[*] Loaded {len(EMOJI_POOL)} emojis in the pool.")

print("[*] Building solver cache...")
solver_cache = build_solver_cache(FONT_PATH, EMOJI_POOL_PATH)


io = remote(HOST, PORT)
io.sendlineafter(b"> ", b"2")

failed = False
for _ in range(ROUND):
    io.recvuntil(b"Round: ")
    round_num = int(io.recvline().decode().split("/")[0].strip())
    print(f"[+] Round: {round_num}/{ROUND}")

    io.recvuntil(b"Here is your CAPTCHA:\n")
    captcha_data = io.recvline().decode().strip()
    captcha_bytes = base64.b64decode(captcha_data)

    solution = solve_captcha(captcha_bytes, solver_cache)
    io.sendlineafter(b">>> ", solution.encode())

    io.recvline()
    result = io.recvline().decode().strip()
    print(result)

    if "Correct!" not in result:
        failed = True
        break

if failed:
    print("[-] Failed to solve the CAPTCHA.")
else:
    print(f"[+] Successfully completed all rounds!")

io.interactive()
io.close()
