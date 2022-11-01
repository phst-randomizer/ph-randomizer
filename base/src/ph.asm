; This file associates the labels in `ph.h` with actual memory addresses in the ROM;
; this enables them to be called from C code.

.definelabel strlen, 0x2046fc4
.definelabel strcpy, 0x2046fe0
.definelabel strcat, 0x20470f8
.definelabel sprintf, 0x200c8d0
.definelabel get_npc_address, 0x203e824
