; This code will be executed immediately after a save file is loaded.
; Any flags that need to be set in memory can be set here.

push r0, r2, r3, r4 ; preserve original register values

; Set r0 to the offset where flags start. In the vanilla rom, this is 0x21b553c.
; This is likely heap-allocated though, so the offset may change as we make modifications to the rom.
; So, we can't just use a constant. Luckily the link register contains the offset we need at this point,
; though it is offset by 0x30 so we must subtract that first.
sub r4, lr, 0x30

; TODO: Document flags being set below + figure out what other flags need to be set
ldr r0, =0xF73F7FEE
str r0, [r4]

ldr r0, =0xFFFFF8FF
mov r3, 0x4
str r0, [r4, r3]

ldr r0, =0xFD1FFFFF
mov r3, 0x8
str r0, [r4, r3]

ldr r0, =0xFEFE3FDF
mov r3, 0xC
str r0, [r4, r3]

ldr r0, =0x2FFF7FFD
mov r3, 0x10
str r0, [r4, r3]

ldr r0, =0x7FFFFF03
mov r3, 0x14
str r0, [r4, r3]

ldr r0, =0xFFF8C3FE
mov r3, 0x18
str r0, [r4, r3]

ldr r0, =0xFFF5FEF5
mov r3, 0x1C
str r0, [r4, r3]

ldr r0, =0xFFEFF86E
mov r3, 0x20
str r0, [r4, r3]

ldr r0, =0xFFF0003D
mov r3, 0x24
str r0, [r4, r3]

ldr r0, =0xFF0EFFFF
mov r3, 0x28
str r0, [r4, r3]

ldr r0, =0x9FFFFFFD
mov r3, 0x2C
str r0, [r4, r3]

ldr r0, =0x00000037
mov r3, 0x30
str r0, [r4, r3]

pop r0, r2, r3, r4 ; restore original register values
