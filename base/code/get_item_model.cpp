#include "ph.hpp"

#define NEW_DATA_FILE_PATH_PREFIX "r/"

extern "C" {

void get_item_model(u32 item_id, char *nsbmd_dest, char *nsbtx_dest) {
  char *model_name;
  char *model_file_path_prefix = NEW_DATA_FILE_PATH_PREFIX;

  switch (item_id) {
  // These are new item models that are injected into the game by the pre-build base
  // patch. See `_inject_new_get_item_models` in `rebuild_rom.py`. These should
  // match up with the filenames defined there.
  case 0x45:
    model_name = "SwB";
    break;
  default:
    model_name = item_id_to_string[item_id];
    model_file_path_prefix = got_new_item_model_path_prefix;
    break;
  }

  // Otherwise, do default behavior.
  strcpy(nsbmd_dest, model_file_path_prefix);
  strcat(nsbmd_dest, model_name);
  strcat(nsbmd_dest, ".nsbmd");

  strcpy(nsbtx_dest, model_file_path_prefix);
  strcat(nsbtx_dest, model_name);
  strcat(nsbtx_dest, ".nsbtx");
}

} // extern "C"
