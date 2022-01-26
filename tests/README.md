# Tests

This subdirectory contains a suite of tests for the randomizer.

## DeSmuME integration tests

These tests make use of the `py-desmume` Python package to programatically spin up and control a DeSmuME emulator instance. `py-desmume` also allows the programmer to inspect register and memory contents at runtime, making it very simple to write assertions about the state these in tests.

### Using existing save data

It is sometimes desirable to load a battery save prior to running a test. For each pytest function, the testing environment will look for a .dsv file in the `/test/test_data` (relative to root of repository) directory with the same name as the test. For example, for a test function `test_boot_new_game(...)`, placing a battery save file named `test_boot_new_game.dsv` into the previously mentioned directory will cause DeSmuME to load that dsv prior to that test running.
