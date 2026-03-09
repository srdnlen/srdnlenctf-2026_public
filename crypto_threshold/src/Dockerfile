FROM cybersecnatlab/socaz:ubuntu-noble

RUN apt-get update && apt-get install -y python3-pip

COPY ./requirements.txt ./
RUN pip install -r requirements.txt --break-system-packages

COPY ./server.py /home/user/server
COPY ./ring.py /home/user/ring.py
COPY ./ts.py /home/user/ts.py
COPY ./crypto_random.py /home/user/crypto_random.py

WORKDIR /home/user
CMD socaz --timeout 600 --flag-from-env FLAG --bind 1337 --cmd "python3 /home/user/server"
EXPOSE 1337
