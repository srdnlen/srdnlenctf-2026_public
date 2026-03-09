FROM cybersecnatlab/socaz:ubuntu-noble

RUN apt-get update && apt-get install -y python3-pip

COPY ./server.py /home/user/server
COPY ./chall /home/user/chall
COPY ./check_solve /home/user/check_solve

WORKDIR /home/user
RUN ./chall MAYO-2 GENKEY
CMD socaz --timeout 300 --flag-from-env FLAG --bind 1337 --cmd "python3 /home/user/server"
EXPOSE 1337
