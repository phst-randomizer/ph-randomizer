.PHONY: all test lint format clean debug

# Make sure devkitARM is installed
ifeq ($(strip $(DEVKITARM)),)
	$(error "Please set DEVKITARM in your environment. export DEVKITARM=<path to>devkitARM")
endif

# Include devkitARM tool definitions
include $(DEVKITARM)/base_tools

# Set up compilation flags
CFLAGS	:=	-marm -mno-thumb-interwork -march=armv5te -mtune=arm946e-s -fno-inline -Wall -Os

# C source file directory
SRC_DIR=src
# Directory to save compiled files to
DEST_DIR=build
SRC=$(wildcard $(SRC_DIR)/*.c)
OBJ=$(SRC:.c=.o)
ASM=$(SRC:.c=.asm)

INPUT_NDS_FILE=$(PH_ROM_PATH)
OUTPUT_NDS_FILE=out.nds

$(OUTPUT_NDS_FILE): data overlay arm9.bin arm7.bin y9.bin y7.bin banner.bin header.bin
	./ndstool -c out.nds -9 arm9.bin -7 arm7.bin -y9 y9.bin -y7 y7.bin -d data -y overlay -t banner.bin -h header.bin

data: $(INPUT_NDS_FILE)
	./ndstool -x $(INPUT_NDS_FILE) -d data/

arm9.bin overlay: $(INPUT_NDS_FILE) $(OBJ) y9.bin
	./ndstool -x $(INPUT_NDS_FILE) -9 arm9.bin -y overlay/

	# Split arm9.bin into two files - uncompressed and compressed parts
	dd bs=1 skip=0 count=16384 if=arm9.bin of=arm9_header.bin
	dd bs=1 skip=16384 if=arm9.bin of=arm9_original.bin
	truncate -s -12 arm9_original.bin

	# Decompress BLZ-compressed binaries
	./blz -d arm9_original.bin
	for file in $$(cat src/main.asm | grep -oP "overlay_(\d+).bin"); do \
		./blz -d overlay/$$file; \
	done

	# Patch the binaries with our custom code
	./armips src/main.asm

	# Recompress the binaries
	./blz -eo arm9_compressed.bin
	for file in $$(cat src/main.asm | grep -oP "overlay_(\d+).bin"); do \
		./blz -eo overlay/$$file; \
	done

	# Combine arm9.bin back into a single file
	# TODO: Do this in bash instead of an inline python script
	python3 -c "exec(\"\"\"\nimport struct\n\nwith open(\"arm9_compressed.bin\", \"rb\") as input_arm9, open(\n    \"arm9_header.bin\", \"rb\"\n) as input_header, open(\"arm9.bin\", \"wb\") as output_arm9:\n    data = input_header.read() + input_arm9.read()\n    data = data[:0xB78] + struct.pack(\"<I\", len(data) + 0x2000000) + data[0xB7C:]\n    output_arm9.write(data)\n\"\"\")"

	# Update y9.bin to account for new sizes of overlays
	mv fixy9.exe overlay/
	mv y9.bin overlay/
	cd overlay && for file in $$(cat ../src/main.asm | grep -oP "overlay_(\d+).bin"); do \
		echo $$file; \
		/opt/wine-stable/bin/wine fixy9.exe y9.bin $$file; \
	done
	mv overlay/y9.bin .

arm7.bin: $(INPUT_NDS_FILE)
	./ndstool -x $(INPUT_NDS_FILE) -7 arm7.bin

y9.bin: $(INPUT_NDS_FILE)
	./ndstool -x $(INPUT_NDS_FILE) -y9 y9.bin

y7.bin: $(INPUT_NDS_FILE)	
	./ndstool -x $(INPUT_NDS_FILE) -y7 y7.bin

banner.bin: $(INPUT_NDS_FILE)
	./ndstool -x $(INPUT_NDS_FILE) -t banner.bin

header.bin: $(INPUT_NDS_FILE)
	./ndstool -x $(INPUT_NDS_FILE) -h header.bin
# Same as `all`, but also includes readable .asm file
debug: $(OBJ) $(ASM)

# Compile C source file to assembly code
%.asm: %.c
	$(CC) $(CFLAGS) -S "$<" -o "$@" -fverbose-asm

# Compile C source file to object file
%.o: %.c
	$(CC) $(CFLAGS) -c "$<" -o "$@"

.clang-format:
	clang-format-12 --style=llvm --dump-config > .clang-format

lint: $(SRC) .clang-format
	clang-format-12 --dry-run --Werror $(SRC)

format: $(SRC) .clang-format
	clang-format-12 -i --Werror $(SRC)

# Clean up
clean:
	rm -f $(DEST_DIR)/*

all: $(OUTPUT_NDS_FILE)

test: lint
