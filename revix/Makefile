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

# NEGA: make faqat fayl vaqtlariga qaraydi, bayroqlarga EMAS. Stamp bo'lmasa
# sanitizer bilan yig'ilgan `sut` keyingi oddiy `make all` da JIMGINA qayta
# ishlatilardi -- test_sut.py dagi sut_bin fixture TSan/ASan binar'ini
# "haqiqiy" SUT deb ishga tushirardi. SUT vaqt etalon'i (timing reference)
# bo'lgani uchun bu hech qanday signalsiz o'lchovni buzadi.
# Stamp = kompilyator + CFLAGS + EXTRA_CFLAGS (haqiqiy bayroqlar). U FAQAT
# mazmuni o'zgarganda qayta yoziladi (cmp), shuning uchun bayroq bir xil
# bo'lsa mtime o'zgarmaydi va keraksiz qayta kompilyatsiya bo'lmaydi.
# Nomi `*.tmp` ataylab: .gitignore allaqachon `*.tmp` ni qamrab oladi.
STAMP := sut.flags.tmp
BUILD_ID := $(CC) $(CFLAGS) $(EXTRA_CFLAGS)

.PHONY: all clean FORCE

all: $(BIN)

FORCE:

$(STAMP): FORCE
	@printf '%s\n' '$(BUILD_ID)' | cmp -s - $@ || printf '%s\n' '$(BUILD_ID)' > $@

$(BIN): $(SRC) $(STAMP)
	$(CC) $(CFLAGS) $(EXTRA_CFLAGS) -o $@ $<

clean:
	rm -f $(BIN) $(STAMP)
