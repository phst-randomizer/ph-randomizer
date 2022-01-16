.nds
.relativeinclude on
.erroronwarning on

.open "../arm9_original.bin","../arm9_compressed.bin",0x02004000
    .arm
    .org 0x54894 + 0x2004000
        ; Area of unused space in arm9.bin; new code can be stored here
        .area 0x228, 0xFF
            .importobj "src/set_initial_flags.o"
            .importobj "src/faster_boat.o"

            @init_flags:
                sub r0, lr, 0x30 ; set_initial_flags() function parameter
                bl set_initial_flags
                pop r3, pc ; original instruction, do not change

            @faster_boat:
                push lr
                strlt r0,[r4,0x78] ; original instruction, do not change
                bl faster_boat
                pop pc
        .pool
        .endarea
.close


.open "../overlay/overlay_0000.bin", 0x02077360
    .arm
    .org 0x20300 + 0x02077360
        .area 0x4
            b @init_flags
        .endarea
.close


.open "../overlay/overlay_0031.bin", 0x0211F5C0
    .arm
    .org 0x17420 + 0x0211F5C0 ;0x217bce0
        .area 0x4
            bl @faster_boat
        .endarea
.close
