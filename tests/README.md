# Tests

This subdirectory contains a suite of tests for the randomizer written using the `pytest` testing framework.

## Patcher/shuffler tests

These are tests for the randomizer program itself (i.e. the desktop application you run on your PC). For example, these might be unit tests for python functions that are part of the shuffler, integration-style tests that run the randomizer and examine its output, etc. 

### How to run

To run them, install `tox` (`pip install tox`) and run the following from the root of the repo:

`tox -e test`

## DeSmuME integration tests

These tests make use of the `py-desmume` Python package to programatically spin up and control a DeSmuME emulator instance. `py-desmume` also allows the programmer to inspect register and memory contents at runtime, making it very simple to write assertions about the state of these in tests.

Here, we use it to test the base ROM patches that we apply to the ROM before randomizing it - see the `base/` directory for more info.

### How to run

These tests are run in a seperate way from the "regular", non-desmume based tests. To run them, install `tox` (`pip install tox`) and run the following from the root of the repo:

`PH_ROM_PATH="rom.nds" tox -e test-desmume`

(Replace `rom.nds` with the location of your patched ROM)

### Writing tests

All desmume-based tests should be in `test_desmume.py` (although fixtures added for it can be added to `conftest.py`).

#### Using existing save data

It is sometimes desirable to load a battery save prior to running a test. For each pytest function, the testing environment will look for a .dsv file in the `/tests/test_data` (relative to root of repository) directory with the same name as the test. For example, for a test function `test_boot_new_game(...)`, placing a battery save file named `test_boot_new_game.dsv` into the previously mentioned directory will cause DeSmuME to load that dsv prior to that test running.
