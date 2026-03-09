docker: dockerfile.compile
	docker run --rm -t -v .:/challenge `docker build -q -f dockerfile.compile .` /bin/bash -c "cd /challenge && make binary"

binary: main.c
	gcc $^ -o $@ ${WARNINGS} ${NO_BASE_POINTER} ${PARTIAL_RELRO} ${NO_PIE} ${NO_CANARY}


32BIT = -m32
64BIT = -m64

NO_CANARY = -fno-stack-protector
CANARY = -fstack-protector
ALWAYS_CANARY = -fstack-protector-all

NO_NX = -Wl,-z,execstack
NX = -Wl,-z,noexecstack

NO_RELRO = -Wl,-z,norelro
PARTIAL_RELRO = -Wl,-z,lazy
FULL_RELRO = -Wl,-z,now

NO_PIE = -no-pie
PIE = -pie
STATIC = -static
STATIC_PIE = -static-pie

STRIP = -s
DEBUG = -g

NO_BASE_POINTER = -fomit-frame-pointer

WARNINGS = -Wall -Wextra -Wpedantic
EXTRA_WARNINGS = -Wconversion -Wsign-conversion -Wshadow -Wpointer-arith -Wcast-align -Wstrict-prototypes -Wmissing-prototypes -Wold-style-definition -Wmissing-declarations -Wfloat-equal -Wundef -Winline -Wswitch-default -Wswitch-enum -Wunreachable-code -Wformat=2 -Wduplicated-cond -Wduplicated-branches -Wlogical-op -Wnull-dereference -Wjump-misses-init -Wdouble-promotion -Wstrict-overflow=5 -Wcast-qual -Wwrite-strings -Waggregate-return -Wno-unused-parameter -fanalyzer
