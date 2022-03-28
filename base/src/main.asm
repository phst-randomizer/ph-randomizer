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
            .importobj "src/spawn_custom_freestanding_item.o"

            @init_flags:
                sub r0, lr, 0x30 ; set_initial_flags() function parameter
                bl set_initial_flags
                pop r3, pc ; original instruction, do not change

            @faster_boat:
                push lr
                strlt r0,[r4,0x78] ; original instruction, do not change
                bl faster_boat
                pop pc

            @check_additional_items_tree_drop:
                .include "_additional_tree_items.asm"
                ldr r0, [r4, 0x6c]
                b 0x2162790

            .include "_island_shop_files.asm"
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


.open "../overlay/overlay_0029.bin", 0x0211F5C0 ; overlay 14 in ghidra
    .arm
    .org 0x213b0e8
        .area 0x74, 0xFF
            .importobj "src/extend_RUPY_npc.o"
        .endarea

    .org 0x213a108
        .area 0x10, 0x00
            ; patch out check that ensures only keys (id 0x1) can be spawned this way
        .endarea

    .org 0x213a174
        .area 0x4
            bl spawn_custom_freestanding_item
        .endarea
.close


.open "../overlay/overlay_0031.bin", 0x0211F5C0
    .arm
    .org 0x17420 + 0x0211F5C0 ;0x217bce0
        .area 0x4
            bl @faster_boat
        .endarea
.close


.open "../overlay/overlay_0037.bin", 0x0215b400
    .arm
    .org 0x216278c
        .area 0x4, 0xff
            b @check_additional_items_tree_drop
        .endarea
.close

.open "../overlay/overlay_0060.bin", 0x0217bce0
    .arm
    ; Relocate the shop item NSBMD/NSBTX filename strings so that
    ; they can be changed without length overflow issues:
    .org 0x21822b0
        .area 0x4
            .word org(shA_nsbmd)
        .endarea
    .org 0x2182304
        .area 0x4
            .word org(shA_nsbtx)
        .endarea
    .org 0x2182294
        .area 0x4
            .word org(arrowpod_nsbmd)
        .endarea
    .org 0x21822e8
        .area 0x4
            .word org(arrowpod_nsbtx)
        .endarea
    .org 0x21822a8
        .area 0x4
            .word org(minaP_nsbmd)
        .endarea
    .org 0x21822fc
        .area 0x4
            .word org(minaP_nsbtx)
        .endarea
    .org 0x2182298
        .area 0x4
            .word org(bcbagM_nsbmd)
        .endarea
    .org 0x21822ec
        .area 0x4
            .word org(bcbagM_nsbtx)
        .endarea
.close
