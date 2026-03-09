import time
import sys
import PIL
import os

from gen import generate_image
from base64 import b64encode



# --- CONFIGURATION ---
FLAG = os.getenv("FLAG", "srdnlen{REDACTED}")

ROUNDS = 100
TIMEOUT = 8

SAMPLE_SEED = os.getenv("SAMPLE_SEED", "REDACTED")

BANNER = r"""
##########################################################################################
#      ______                    _  _    _____               _         _                 #
#     |  ____|                  (_)(_)  / ____|             | |       | |                #
#     | |__    _ __ ___    ___   _  _  | |      __ _  _ __  | |_  ___ | |__    __ _      #
#     |  __|  | '_ ` _ \  / _ \ | || | | |     / _` || '_ \ | __|/ __|| '_ \  / _` |     #
#     | |____ | | | | | || (_) || || | | |____| (_| || |_) || |_| (__ | | | || (_| |     #
#     |______||_| |_| |_| \___/ | ||_|  \_____|\__,_|| .__/  \__|\___||_| |_| \__,_|     #
#                              _/ |                  | |                                 #
#                             |__/                   |_|        (Author: @uNickz)        #
#                                                                                        #
##########################################################################################
"""



def get_sample(seed: str) -> None:
    print("--- Sample CAPTCHA ---")
    print()

    try:
        image_bytes, expected_solution = generate_image(seed)
    except Exception:
        print("[!] Internal server error during image generation. Please contact an admin.")
        sys.exit(1)

    print("Here is your sample CAPTCHA:")
    print(b64encode(image_bytes).decode("utf-8"))
    print()
    print(f"Expected solution for the sample CAPTCHA: {expected_solution}")



def start_challenge() -> None:
    for round_num in range(1, ROUNDS + 1):
        print(f"--- Round: {round_num}/{ROUNDS} ---")
        print()

        try:
            image_bytes, expected_solution = generate_image()
        except Exception:
            print("\n[!] Internal server error during image generation. Please contact an admin.")
            sys.exit(1)

        start_time = time.perf_counter()

        print("Here is your CAPTCHA:")
        print(b64encode(image_bytes).decode("utf-8"))
        user_answer = input(">>> ").strip()

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        if elapsed_time > TIMEOUT:
            print("\n[!] Time's up! Come on, you can do better than that!")
            print("Connection terminated. Goodbye!")
            sys.exit(0)

        if user_answer.upper() != expected_solution.upper():
            print("\n[!] Wrong answer! Come on, you can do better than that!")
            print("Connection terminated. Goodbye!")
            sys.exit(0)

        if round_num < ROUNDS:
            print(f"\n[+] Correct! Be ready for the next one...")
        else:
            print(f"\n[+] Correct!")
        print()

    print("================================================================")
    print("Congratulations! You solved all the CAPTCHAs and earned the flag!")
    print(f"Here is your reward: {FLAG}")
    print("================================================================")



def main() -> None:
    print(BANNER)
    print(f"Will you be able to solve {ROUNDS} CAPTCHAs in a row to get the flag?")
    print("For each CAPTCHA, you will receive a base64-encoded PNG image containing a set of random emojis.")
    print("Emojis are randomly rotated by a real-valued angle in the range [0°, 360°).")
    print(f"You must identify all emojis within {int(TIMEOUT)} seconds.")
    print("Submit your answer as fully-qualified Unicode codepoints in hexadecimal.")
    print("Separate emojis with spaces and use hyphens as separators for multi-codepoint emojis.")
    print("Example with 3 emojis (😀 ☺️ 😶‍🌫️): 1F600 263A-FE0F 1F636-200D-1F32B-FE0F")
    print()

    while True:
        print("--- Main Menu ---")
        print()
        print("[i] Choose an option:")
        print("  1. Get sample CAPTCHA.")
        print("  2. Start challenge.")
        print("  3. About.")
        print("  4. Exit.")

        choice = input("> ").strip()
        print()

        if choice == "1":
            get_sample(SAMPLE_SEED)
        elif choice == "2":
            start_challenge()
        elif choice == "3":
            print(f"Will you be able to solve {ROUNDS} CAPTCHAs in a row to get the flag?")
            print("For each CAPTCHA, you will receive a base64-encoded PNG image containing a set of random emojis.")
            print("Emojis are randomly rotated by a real-valued angle in the range [0°, 360°).")
            print(f"You must identify all emojis within {int(TIMEOUT)} seconds.")
            print("Submit your answer as fully-qualified Unicode codepoints in hexadecimal.")
            print("Separate emojis with spaces and use hyphens as separators for multi-codepoint emojis.")
            print("Example with 3 emojis (😀 ☺️ 😶‍🌫️): 1F600 263A-FE0F 1F636-200D-1F32B-FE0F")
            print()
            print(f"Images are rendered using Pillow: v{PIL.__version__}.")
            print()
            print("The font used to render the emojis is available here:")
            print("https://github.com/PoomSmart/EmojiLibrary/releases/download/0.18.4/AppleColorEmoji-160px.ttf")
            print()
            print("You can find the full list of emojis and their Unicode codepoints here:")
            print("https://unicode.org/Public/emoji/latest/emoji-test.txt")
        elif choice == "4":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

        print()



if __name__ == "__main__":
    main()