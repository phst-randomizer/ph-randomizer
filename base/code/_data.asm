.open "../data/English/Message/regular.bmg", 0x23DF010
    .arm
    .org 0x23DF230
        .align
        item_flags:
        .importobj "code/_item_model_mapping.o"
.close
