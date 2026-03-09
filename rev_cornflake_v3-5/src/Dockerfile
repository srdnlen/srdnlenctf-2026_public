FROM cybersecnatlab/socaz:python-3.12-bookworm


RUN apt-get clean
RUN apt-get update
RUN apt-get install -y socat
RUN rm -rf /var/lib/apt/lists/*

RUN useradd userchall
WORKDIR /challenge

COPY --chown=root:root ./c2_server.py .
COPY --chown=root:root --chmod=004 ./payload.dll .


EXPOSE 8000


ENTRYPOINT ["socat", "-t", "300", "-T", "20", "TCP-LISTEN:8000,reuseaddr,nodelay,fork", "EXEC:'python3 -u c2_server.py'"]