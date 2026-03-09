import sys
import binascii

# --- Configuration ---
TARGET_USERNAME = b"super_powerful_admin"
RC4_KEY = b"s3cr3t_k3y_v1" 
PAYLOAD_FILE = "payload.dll"

def rc4_crypt(data, key):
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

def send_http_response(status_code, body=b""):
    status_msg = "OK" if status_code == 200 else "Forbidden"
    headers = [
        f"HTTP/1.1 {status_code} {status_msg}",
        "Content-Type: application/x-msdownload",
        f"Content-Length: {len(body)}",
        "Connection: close", 
        "", 
    ]
    response_header = "\r\n".join(headers)
    
    # Write to stdout (network)
    try:
        sys.stdout.buffer.write(response_header.encode() + b"\r\n")
        if body:
            sys.stdout.buffer.write(body)
        sys.stdout.buffer.flush()
    except BrokenPipeError:
        pass # Client disconnected, that's fine

def main():
    # Read from STDIN
    try:
        # We try to read the first line (GET /...)
        # If the pipe is empty/broken immediately, this will raise exception
        request_line = sys.stdin.readline()
        
        # If readline returns empty string, connection is dead
        if not request_line: 
            return
            
    except Exception as e:
        sys.stderr.write(f"Input Error: {e}\n")
        return

    # Extract SessionID
    session_id_hex = None
    if "SessionID=" in request_line:
        try:
            parts = request_line.split("SessionID=")
            if len(parts) > 1:
                session_id_hex = parts[1].split()[0].split("&")[0]
        except:
            pass

    if session_id_hex:
        try:
            encrypted_data = binascii.unhexlify(session_id_hex)
            decrypted_username = rc4_crypt(encrypted_data, RC4_KEY)
            
            # Debug to stderr (Docker logs)
            sys.stderr.write(f"Decrypted: {decrypted_username}\n")

            if decrypted_username == TARGET_USERNAME:
                try:
                    with open(PAYLOAD_FILE, 'rb') as f:
                        payload_data = f.read()
                    send_http_response(200, payload_data)
                    return
                except FileNotFoundError:
                    sys.stderr.write("Error: payload.dll not found\n")
        except Exception as e:
            sys.stderr.write(f"Crypto Error: {e}\n")

    send_http_response(403)

if __name__ == "__main__":
    main()
    