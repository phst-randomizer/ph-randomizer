# Contributing to the randomizer

Note, this document is very much a work-in-progress.

## Code style/formatting guidelines

All code is linted and, in the case of Python, type-checked in CI on every commit. To run these checks locally, make sure you have `tox` installed:

`pip install tox`

and simply run `tox` in the root of the repository.

You can also auto-format your code with `tox -e format`. It won't fix every linting error, but it will fix most.

It's recommended that you run `tox -e format` and `tox` prior to opening a PR to avoid unexpected CI failures.


## Automated testing

Note, this section summarizes the testing philosophy of the randomizer and gives a brief overview of the testing infrastructure. For information on how to write or run these tests, see `tests/README.md`.

Several automated tests exist to verify the correctness and exercise various parts of the randomizer. They are written in Python using the `pytest`
testing framework and are located in the `tests/` directory.

There are two distinct classes of automated tests used to test the randomizer.

1) General unit/integration-style tests that test parts of the randomizer application code like the shuffler, patcher, and UI.

2) Tests that spin up a live instance of the DeSmuME emulator that actually runs a copy of the ROM that has been patched in some way by the randomizer, while issuing commands to it and making assertions about the state of RAM and/or CPU registers. These are mostly used to test the base ROM patches, since realistically the only way to test those is to apply them to a real ROM and run it to make sure it behaves as expected.

Generally, the former type of test is easy to write and very cheap in the sense that, when done right, they have a low maintenance burden while providing a high value in terms of catching bugs. It's usually a good idea to have at least one of these tests if adding a new feature to the randomizer. 

The latter type of test tends to be the opposite, in that they are usually difficult to write and can introduce a significant maintenance burden. You're essentially giving an emulator a series of buttons and touch screen coordinates to hit and then making assertions about the state of the game's memory based on them, which doesn't translate into easily readable code. Tests of this kind should probably be kept to a minimum, and only written for crucial components of the randomizer that cannot be tested with the former, more conventional approach (such as the base ROM patches). In any case, it's best to discuss with the randomizer team before writing one.
