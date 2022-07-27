; Check if the ID from the ZMB file is less than or equal to 0x7 (the max id in the vanilla rom)
; If it is, return from here and continue executing the existing function.
ldr r0, [r4, 0x6c]
cmp r0, 0x7
ble @@return

; Otherwise, spawn a RUPY using the ZMB ID as the rupy_type.
ldr r0, =0x2162c00
ldr r0, [r0]
ldrsh r1, [r4, 0x34]
ldr r0, [r0]
bl 0x2084c68
add r0, sp, 0x4
bl 0x20c14a0
mvn r1, 0x0
add r0, sp, 0x4
str r1, [sp, 0x20]
str r1, [sp, 0x24]
bl 0x20c32e8

; NOTE: this differs from the original RUPY spawning code.
; Instead of copying in a specific "RUPY type id", we're just passing the ZMB
; item id with the MSB set
ldr r0, [r4, 0x6c] ; just copy id into r0

strh r0, [sp, 0x4]
mov r1, 0x0
str r1, [sp, 0x0]
ldr r0, =0x2162c04
ldr r0, [r0]
ldr r1, =0x2162c18
ldr r1, [r1]
ldr r0, [r0, 0x0]
add r2, sp, 0x144
add r3, sp, 0x4
bl 0x20c3fe8
ldr r0, =0x2162c00
ldr r0, [r0]
ldrsh r1, [r4, 0x34]
ldr r0, [r0, 0x0]
mov r2, 0x1
bl 0x2084c50

@@return:
