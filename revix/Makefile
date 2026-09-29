# REVIX SUT build.
#
# Bog'liqlik YO'Q: libsystemd'ga link qilinmaydi (sd_notify sut.c ichida).
# Repo ataylab yangi bog'liqlik qo'shmaydi -- reproducibility narxi.
#
# -Werror ataylab: SUT o'lchov asbobi. Ogohlantirishlar (masalan format yoki
# imzo taqqoslash) bu yerda jim o'tkazilsa, ular o'lchov xatosiga aylanadi.

CC ?= cc
CFLAGS := -O2 -Wall -Wextra -Werror -std=c11 -pthread
EXTRA_CFLAGS ?=

BIN := sut
SRC := sut.c

.PHONY: all clean

all: $(BIN)

$(BIN): $(SRC)
	$(CC) $(CFLAGS) $(EXTRA_CFLAGS) -o $@ $<

clean:
	rm -f $(BIN)
