#include "ph.h"
#include <stdint.h>

void get_item_model(uint32_t item_id, char *nsbmd_dest, char *nsbtx_dest, char **item_mapping) {
  char *model_name = item_mapping[item_id];
  int32_t length = strlen(model_name);

  // If it contains a '.', assume it ends in .bmg and that it's an overwritten custom model.
  for (int i = 0; i < length; i++) {
    if (model_name[i] == '.') {
      strcpy(nsbmd_dest, "Spanish/Message/");
      strcat(nsbmd_dest, model_name);
      strcpy(nsbtx_dest, "French/Message/");
      strcat(nsbtx_dest, model_name);
      return;
    }
  }

  // Otherwise, do default behavior.
  char *file_path_prefix = "Player/get/gd_";

  strcpy(nsbmd_dest, file_path_prefix);
  strcat(nsbmd_dest, model_name);
  strcat(nsbmd_dest, ".nsbmd");

  strcpy(nsbtx_dest, file_path_prefix);
  strcat(nsbtx_dest, model_name);
  strcat(nsbtx_dest, ".nsbtx");
}
