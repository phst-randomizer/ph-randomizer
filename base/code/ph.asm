; This file associates the labels in `ph.h` with actual memory addresses in the ROM;
; this enables them to be called from C code.

.definelabel strlen, 0x2046fc4
.definelabel strcpy, 0x2046fe0
.definelabel strncpy, 0x20470a8
.definelabel strcat, 0x20470f8
.definelabel strcmp, 0x2047128
.definelabel strncmp, 0x204723c
.definelabel strrchr, 0x2047270
.definelabel strstr, 0x20472ac
.definelabel sprintf, 0x200c8d0
.definelabel LoadOverlay, 0x2042348
.definelabel get_npc_address, 0x203e824
.definelabel got_new_item_model_path_prefix, 0x20e5da8
.definelabel item_id_to_string, 0x20e5c3c
