.open "../data/English/Message/regular.bmg", 0x0
    .arm
    .org 0x220
        .asciiz "RANDOMIZER_DATA_START   "
        .importobj "code/_flags.o"
        .asciiz "RANDOMIZER_DATA_END"
.close
