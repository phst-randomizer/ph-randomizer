#include "_flags.h"
#include "rando_settings.h"

#define NO_SETTING -1, 0

Flag flags[] = {
    {0x0, 0x2, NO_SETTING},  // celia dialogue after getting oshus sword
    {0x0, 0x4, NO_SETTING},  // completed oshus sword tutorial
    {0x0, 0x8, NO_SETTING},  // talked to mercay bartender about linebeck
    {0x0, 0x20, NO_SETTING}, // talked to oshus after seeing red chuchus
    {0x0, 0x40, NO_SETTING}, // showed linebeck the SW sea chart after ToTOK
    {0x0, 0x80, NO_SETTING}, // set sail for the first time (linebeck dialog)
    {0x2, 0x2, MERCAY_BRIDGE_REPAIRED_FROM_START}, // mercay bridge repaired
    {0x18, 0x2, NO_SETTING},                       // TALKED_TO_OSHUS_FIRST_TIME
    {0x2c, 0x1, NO_SETTING},  // saw broken mercay bridge for first time
    {0x26, 0x10, NO_SETTING}, // uncharted island bridge is extended
};
