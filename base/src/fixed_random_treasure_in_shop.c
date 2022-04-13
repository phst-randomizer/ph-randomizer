#include <stdint.h>

__attribute__((target("thumb"))) void
fixed_random_treasure_in_shop(char *stack_ptr, char *nsbmd_file,
                              char *nsbtx_file) {
  for (int i = 0; i < 30; i++) {
    stack_ptr[i + 0x1C] = nsbtx_file[i];
    stack_ptr[i + 0x44] = nsbmd_file[i];
  }
}
