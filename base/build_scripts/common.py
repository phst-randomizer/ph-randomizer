import os

# overlays to be modified. The build script uses this to determine what overlays
# to decompress/compress when building the base rom patch.
overlays_to_modify = ("0000", "0022", "0031", "0037")

ARMIPS_EXECUTABLE_PATH = os.environ["ARMIPS_EXECUTABLE_PATH"]
BLZ_EXECUTABLE_PATH = os.environ["BLZ_EXECUTABLE_PATH"]
FIXY9_EXECUTABLE_PATH = os.environ["FIXY9_EXECUTABLE_PATH"]
NDSTOOL_EXECUTABLE_PATH = os.environ["NDSTOOL_EXECUTABLE_PATH"]
