CFLAGS ?= -g
CFLAGS += -Wall
CPPFLAGS += -DBE_DEBUG

all: test

test: bencode.o

clean:
	rm -f *.o core test

.PHONY: all clean
