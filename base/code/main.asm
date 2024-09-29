.nds
.relativeinclude on
.erroronwarning on

.include "ph.asm"

.open "../arm9_original.bin","../arm9_compressed.bin",0x02004000
    .arm
    .org 0x54180 + 0x2004000
        ; Area of unused space in arm9.bin; new code can be stored here
        .area 0x301, 0xFF
            .fill 0xA, 0x0 ; bitmap for randomizer settings

            .include "_island_shop_files.asm"
        .pool
        .endarea

    .org 0x54894 + 0x2004000
        ; Area of unused space in arm9.bin; new code can be stored here
        .area 0x228, 0xFF
            .arm
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

            @spawn_dig_item:
                ; Set rupy_id to id of item we want to spawn | 0x8000 (i.e. with MSB set).
                ; See `extend_RUPY_npc.c` for why this works.
                orr r0, r5, 0x8000
                strh r0, [sp, 0x2c]
                ; Load r4 with "RUPY" string
                ldr r4, =0x212f4c4
                ldr r4, [r4]
                ; Jump to end of switch statement which will end up calling spawn_npc function
                ; with the parameters that we have set here
                b 0x212f3d8

            .thumb
            @load_extra_overlay:
                ; make original function call
                bl 0x202FF40

                ; load new overlay
                ldr r0, =org(@@ExtraOverlay)
                bl LoadOverlay

                ; original instruction. jumps back to normal game code
                pop r3, r4, r5, r6, r7, pc

                ; This is just an instance of an `Overlay` struct, see `ph.h` for its definition
                @@ExtraOverlay:
                    .word 62
                    .word 0x23C0900
                    .word 32512
                    .word 0
                    .word 0
                    .word 0
                    .word 2836
                    .word 32512

            .thumb
            @extend_give_item_function:
                push lr
                ; preserve scratch registers since we're interrupting a running function
                push r0, r1, r2, r3
                blx extend_give_item_function
                pop r0, r1, r2, r3

                ; original instructions. jumps back to normal game code
                ldr r0, =0x20ae244
                mov r1, 0x7d
                ldr r0, [r0]
                pop pc
        .pool
        .endarea

    .org 0x202ffec
        .thumb
        .area 0x6, 0x00
            bl @load_extra_overlay
        .endarea
.close


.open "../overlay/overlay_0000.bin", 0x02077360
    .arm
    .org 0x20300 + 0x02077360
        .area 0x4
            b @init_flags
        .endarea

    .thumb
    .org 0x20ade1c
        ; Overwrite code that gives the player the oshus sword to be progressive
        .area 0xC, 0x00
            ; Save scratch registers, since gcc doesn't do it
            push r0, r1, r2, r3
            bl progressive_sword_check
            pop r0, r1, r2, r3
        .endarea

    .thumb
    .org 0x20adbcc
        .area 0x36, 0x00
            ; Get current item id
            mov r0, 0x46
            lsl r0, r0, 0x2
            add r0, r0, r5
            ldr r0, [r0]

            add r1, sp, 0x8c ; get dest address for nsbmd
            add r2, sp, 0xc ; get dest address for nsbtx

            blx get_item_model

            b 0x20ADC02
        .pool
        .endarea

    .thumb
    .org 0x20ae1c2
        .area 0x6, 0x00
            bl @extend_give_item_function
        .endarea

.close

.open "../overlay/overlay_0003.bin", 0x20eece0
    .arm
    ; update "got item" text ids for:
    .org 0x20ffb90 ; progressive sword
        .area 0x4, 0x0
          .byte 0x8a
        .endarea
    .org 0x20ffba4 ; bow
        .area 0x4, 0x0
          .byte 0x8b
        .endarea
    .org 0x20ffbb8 ; shovel
        .area 0x4, 0x0
          .byte 0x8c
        .endarea
    .org 0x20ffbbc ; bombchus
        .area 0x4, 0x0
          .byte 0x8d
        .endarea
    ;.org 0xffffff ; crimsonine
    ;    .area 0x4, 0x0
    ;      .byte 0x8e
    ;    .endarea
    .org 0x20ffbb4 ; boomerang
        .area 0x4, 0x0
          .byte 0x8f
        .endarea
    .org 0x20ffbd0 ; sea charts (SW/NW/SE/NE)
        .area 0xf, 0x0
          .byte 0x90,0,0,0, 0x91,0,0,0, 0x92,0,0,0, 0x93
        .endarea
    .org 0x20ffc00 ; hammer
        .area 0x4, 0x0
          .byte 0x94
        .endarea
    .org 0x20ffc34 ; king key
        .area 0x4, 0x0
          .byte 0x95
        .endarea
    ;.org 0xffffff ; aquanine
    ;    .area 0x4, 0x0
    ;      .byte 0x96
    ;    .endarea
    .org 0x20ffc04 ; grappling hook
        .area 0x4, 0x0
          .byte 0x97
        .endarea
    ;.org 0xffffff ; azurine
    ;    .area 0x4, 0x0
    ;      .byte 0x98
    ;    .endarea
    .org 0x20ffc14 ; fishing rod
        .area 0x4, 0x0
          .byte 0x99
        .endarea
    .org 0x20ffc18 ; cannon
        .area 0x4, 0x0
          .byte 0x9a
        .endarea
    .org 0x20ffc78 ; salvage arm
        .area 0x4, 0x0
          .byte 0x9b
        .endarea
    ;.org 0xffffff ; sun key
    ;    .area 0x4, 0x0
    ;      .byte 0x9c
    ;    .endarea
    ;.org 0xffffff ; ghost key
    ;    .area 0x4, 0x0
    ;      .byte 0x9d
    ;    .endarea
    .org 0x20ffc74 ; regal necklace
        .area 0x4, 0x0
          .byte 0x9e
        .endarea
.close

.open "../overlay/overlay_0009.bin", 0x02112ba0
    .thumb
    .org 0x211c09a
        ; This overrides the routine that is in charge of spawning the correct 3D model
        ; for the randomized treasure item in the shop. This code disables this
        ; clock-based randomization and makes it a fixed item.
        ; This code handles setting the 3D model (i.e. appearence only), see section for
        ; overlay 60 for the code that actually sets the item id.
        ;
        ; TODO: this causes a crash when running on an actual DS (not in emulation, though),
        ; so disable it for now.
        // .area 0x1C, 0x00
        //     mov r0, sp
        //     ldr r1, =org(random_treasure_nsbmd)
        //     ldr r2, =org(random_treasure_nsbtx)
        //     bl fixed_random_treasure_in_shop
        //     .pool
        // .endarea
.close


.open "../overlay/overlay_0014.bin", 0x0211F5C0
    .arm
    .org 0x213b0e8
        .area 0x74, 0xFF
            .importobj "code/extend_RUPY_npc.o"
        .endarea

    .org 0x213a108
        .area 0x10, 0x00
            ; patch out check that ensures only keys (id 0x1) can be spawned this way
        .endarea

    // TODO: this causes crashes sometimes. Disable for now.
    // .org 0x213a174
    //     .area 0x4
    //         bl spawn_custom_freestanding_item
    //     .endarea

    ; There is essentially a giant `switch` statement in the game code that determines which item
    ; id's are "valid" and able to be spawned from a shovel dig spot. For "invalid" items like
    ; the sword (id=0x3), the case statement looks like this:
    ;
    ;    switch (item_id) {
    ;      case 0x2: # a rupee, which a valid item
    ;        goto SPAWN_NPC
    ;      case 0x3: # a sword, invalid item
    ;        return
    ;      case 0x4: # a shield, invalid item
    ;        return
    ;      .....
    ;      case 0x9: # a big green rupee, valid item
    ;        *rupy_id = 0x3
    ;         goto SPAWN_NPC
    ;    }
    ;
    ; Below, we override each of those "invalid" item cases to look something like this:
    ;
    ;   case 0x3:
    ;     *rupy_id = 0x3 | 0x8000
    ;     goto SPAWN_NPC
    ;   case 0x4:
    ;     *rupy_id = 0x4 | 0x8000
    ;     goto SPAWN_NPC
    ;
    ;   ... and so on. See extend_RUPY_npc.c to see why we're OR'ing 0x8000 here.

    ; sword (0x3)
    .org 0x212f184
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; shield (0x4)
    .org 0x212f188
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; ?? (0x5)
    .org 0x212f18c
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; Bombs (0x7)
    .org 0x212f194
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; Bow (0x8)
    .org 0x212f198
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; Heart container (0xa)
    .org 0x212f1a0
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; ?? (0xb)
    .org 0x212f1a4
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; Boomerang (0xc)
    .org 0x212f1a8
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; Shovel (0xd)
    .org 0x212f1ac
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; Bombchus (0xe)
    .org 0x212f1b0
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; Boss key (0xf)
    .org 0x212f1b4
        .area 0x4
            b @spawn_dig_item
        .endarea
    ; Enable items with ids in range [0x1c, 0x4b] to be spawned from dig spots
    .org 0x212f1e0
        .area 0x8
            b @spawn_dig_item
        .endarea
    ; Enable items with ids greater than 0x61 to be spawned from dig spots
    .org 0x212f3d0
        .area 0x8
            b @spawn_dig_item
        .endarea

.close


.open "../overlay/overlay_0015.bin", 0x0211F5C0
    .arm
    .org 0x17420 + 0x0211F5C0 ;0x217bce0
        .area 0x4
            bl @faster_boat
        .endarea
    ; Patch salvage item item-giving function so that any item can be given
    .org 0x2146430
        .area 0xC, 0x0
            bl custom_salvage_item
        .endarea
.close


.open "../overlay/overlay_0018.bin", 0x0215b400
    .arm
    .org 0x216278c
        .area 0x4, 0xff
            b @check_additional_items_tree_drop
        .endarea
.close

.open "../overlay/overlay_0031.bin", 0x0217bce0
    .arm

    ; Make the "random treasure" in shops a fixed item (i.e. "unrandomize" it)
    ; This defaults it to item id 0x30 (pink coral), but it can be changed
    ; by the patcher. Either way, we don't want date-randomized items
    ; for the purposes of the randomizer.
    .org 0x21801dc
        .area 0x10, 0x00
            mov r0, 0x0
        .endarea
    .org 0x217ec34
        .area 0x4
            mov r1, 0x30
        .endarea

    ; Relocate the shop item NSBMD/NSBTX filename strings so that
    ; they can be changed without length overflow issues:
    .org 0x21822b0
        .area 0x4
            .word org(shA_nsbmd) ; progressive sword
        .endarea
    .org 0x2182304
        .area 0x4
            .word org(shA_nsbtx)
        .endarea
    .org 0x2182290
        .area 0x4
            .word org(bmbagM_nsbmd) ; bomb bag upgrade
        .endarea
    .org 0x21822e4
        .area 0x4
            .word org(bmbagM_nsbtx)
        .endarea
    .org 0x218228c
        .area 0x4
            .word org(heart_utu_nsbmd) ; heart container
        .endarea
    .org 0x21822e0
        .area 0x4
            .word org(heart_utu_nsbtx)
        .endarea
    .org 0x2182294
        .area 0x4
            .word org(arrowpod_nsbmd) ; quiver
        .endarea
    .org 0x21822e8
        .area 0x4
            .word org(arrowpod_nsbtx)
        .endarea
    .org 0x21822ac
        .area 0x4
            .word org(minaC_nsbmd) ; wisdom gem
        .endarea
    .org 0x2182300
        .area 0x4
            .word org(minaC_nsbtx)
        .endarea
    .org 0x21822a8
        .area 0x4
            .word org(minaP_nsbmd) ; power gem
        .endarea
    .org 0x21822fc
        .area 0x4
            .word org(minaP_nsbtx)
        .endarea
    .org 0x21822a4
        .area 0x4
            .word org(minaY_nsbmd) ; courage gem
        .endarea
    .org 0x21822f8
        .area 0x4
            .word org(minaY_nsbtx)
        .endarea
    .org 0x2182298
        .area 0x4
            .word org(bcbagM_nsbmd) ; bombchu bag upgrade
        .endarea
    .org 0x21822ec
        .area 0x4
            .word org(bcbagM_nsbtx)
        .endarea
.close

; Note: this is an extra overlay added by the randomizer.
; It is not present in the original rom, and must be added prior
; to executing this ARMIPS patch.
.open "../overlay/overlay_0062.bin", 0x23C0900
    .org 0x23C0900
        .area 32512, 0xEE
            .arm
            .importobj "code/faster_boat.o"
            .importobj "code/fixed_random_treasure_in_shop.o"
            .importobj "code/progressive_sword_check.o"
            .importobj "code/rando_settings.o"
            .importobj "code/get_item_model.o"
            .importobj "code/set_initial_flags.o"
            .importobj "code/spawn_custom_freestanding_item.o"
            .importobj "code/custom_salvage_item.o"
            .importobj "code/extend_give_item_function.o"
        .endarea
.close
