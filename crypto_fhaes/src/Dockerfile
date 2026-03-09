FROM cybersecnatlab/socaz:ubuntu-noble

RUN apt-get update && apt-get install -y python3-pip

COPY ./requirements.txt ./
RUN pip install -r requirements.txt --break-system-packages

COPY ./server.py /home/user/server
COPY ./fhaes.py /home/user/fhaes.py
COPY ./common.py /home/user/common.py
COPY ./srdnlengarble /home/user/srdnlengarble

WORKDIR /home/user
CMD socaz --timeout 300 --flag-from-env FLAG --bind 1337 --cmd "python3 /home/user/server"
EXPOSE 1337
