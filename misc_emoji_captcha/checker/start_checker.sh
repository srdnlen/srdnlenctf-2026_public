#!/bin/bash

# Run checker inside the container
docker run --rm \
    -v "$(pwd):/app" \
    -e TERM=xterm-256color \
    ctf-emoji-env python3 checker.py
