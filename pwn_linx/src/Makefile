CC = gcc
CFLAGS = -g -Wall -Wextra
LDFLAGS = -Wl,-z,relro,-z,now

TARGET_DIR = build
SRC = linx.c
OUT = linx
TARGET = $(TARGET_DIR)/$(OUT)

all: $(TARGET)

$(TARGET_DIR):
	mkdir -p $@

$(TARGET): $(TARGET_DIR) $(SRC)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)

run: $(TARGET)
	./$<

.PHONY: all
