.open "../data/English/Message/regular.bmg", 0x23DF010
    .arm
    .org 0x23DF230
        .asciiz "RANDOMIZER_DATA_START   "
        .importobj "code/_flags.o"
        .asciiz "RANDOMIZER_DATA_END"

        .align
        item_flags:
        .importobj "code/_item_model_mapping.o"
.close
