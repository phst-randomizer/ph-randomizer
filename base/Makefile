.SUFFIXES:
.PHONY:

# Make sure devkitARM is installed
ifeq ($(strip $(DEVKITARM)),)
	$(error "Please set DEVKITARM in your environment. export DEVKITARM=<path to>devkitARM")
endif

# Include devkitARM tool definitions
include $(DEVKITARM)/base_tools

# Set up compilation flags
CFLAGS	:=	-marm -mno-thumb-interwork -march=armv5te -mtune=arm946e-s -fno-inline -Wall -Os

# Set up source/output directories

# C source file directory
SRC_DIR=src

# Directory to save compiled files to
DEST_DIR=build

SRC=$(wildcard $(SRC_DIR)/*.c)
OBJ=$(SRC:.c=.o)
ASM=$(SRC:.c=.asm)

# Build targets

# Compile all C source files into object files
all: $(OBJ)

# Same as `all`, but also includes readable .asm file
debug: $(OBJ) $(ASM)

# Compile C source file to assembly code
%.asm: %.c
	$(CC) $(CFLAGS) -S "$<" -o "$@" -fverbose-asm
	mkdir -p $(DEST_DIR)
	mv "$@" $(DEST_DIR)

# Compile C source file to object file
%.o: %.c
	$(CC) $(CFLAGS) -c "$<" -o "$@"
	mkdir -p $(DEST_DIR)
	mv "$@" $(DEST_DIR)

.clang-format:
	clang-format-12 --style=llvm --dump-config > .clang-format

lint: $(SRC) .clang-format
	clang-format-12 --dry-run --Werror $(SRC)

format: $(SRC) .clang-format
	clang-format-12 -i --Werror $(SRC)

# Clean up
clean:
	rm -f $(DEST_DIR)/*
