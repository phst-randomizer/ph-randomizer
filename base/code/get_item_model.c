#include "ph.h"
#include <stdint.h>

void get_item_model(uint32_t item_id, char *nsbmd_dest, char *nsbtx_dest) {
  char *model_name = item_id_to_string[item_id];

  // Otherwise, do default behavior.
  strcpy(nsbmd_dest, got_new_item_model_path_prefix);
  strcat(nsbmd_dest, model_name);
  strcat(nsbmd_dest, ".nsbmd");

  strcpy(nsbtx_dest, got_new_item_model_path_prefix);
  strcat(nsbtx_dest, model_name);
  strcat(nsbtx_dest, ".nsbtx");
}
