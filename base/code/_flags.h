#include <stdbool.h>
#include <stdint.h>

typedef struct {
  uint16_t flag_offset;   // offset of the flag from the "base address" (see first
                          // arg of set_initial_flags() )
  uint8_t flag_bit;       // the bit within the value @ flag_offset that represents
                          // this flag
  int32_t setting_offset; // offset of the randomizer setting that this flag is
                          // gated behind, or -1 if it's not gated behind any
                          // settings. Make this a 32 bit uint to pad struct to
                          // 16 bytes
  uint8_t setting_bit;    // the bit within the value @ setting_offset that this
                          // represents this setting
} Flag;

extern Flag flags[];
