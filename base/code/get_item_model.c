#include "ph.h"
#include <stdint.h>

void get_item_model(uint32_t item_id, char *nsbmd_dest, char *nsbtx_dest, char **item_mapping) {
  char *file_path_prefix = "Player/get/gd_";

  strcpy(nsbmd_dest, file_path_prefix);
  strcat(nsbmd_dest, item_mapping[item_id]);
  strcat(nsbmd_dest, ".nsbmd");

  strcpy(nsbtx_dest, file_path_prefix);
  strcat(nsbtx_dest, item_mapping[item_id]);
  strcat(nsbtx_dest, ".nsbtx");
}
