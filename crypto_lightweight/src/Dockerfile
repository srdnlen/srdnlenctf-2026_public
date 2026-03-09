FROM cybersecnatlab/socaz:ubuntu-noble

RUN apt-get update && apt-get install -y build-essential

COPY ./server.c /home/user/server.c

RUN gcc -O3 -o /home/user/server /home/user/server.c

WORKDIR /home/user
CMD socaz --timeout 300 --flag-from-env FLAG --bind 1337 --cmd "/home/user/server"
EXPOSE 1337
