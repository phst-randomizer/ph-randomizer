# Contributing to the randomizer

Note, this document is very much a work-in-progress.

## Running the randomizer from source

Official releases of the randomizer are distributed as single executable files; these are created using [PyInstaller](https://pyinstaller.org). While convenient for end users to run, developers will likely want to run the randomizer from source. To do this:

1. Install the version of [Python](https://www.python.org/downloads/) specified in `.python-version` (Python 3.11 at the time of this writing)
2. Create a virtualenv using whatever tool you prefer
3. Run `pip install -e .` from the root of the repository.
   - It's also recommended to run the following pip install commands if setting up a development environment:
     - `pip install -e .[test]` - installs dependencies needed to run automated tests
     - `pip install -e .[types]` - installs dependencies needed to run type-checking, as well as provide IDE auto-complete for IDE's that support mypy
4. Run `randomizer.py`. Alternatively, to run the shuffler or patcher in isolation, run `shuffler/main.py` or `patcher/main.py`, respectively.

## Code style/formatting guidelines

All code is linted and, in the case of Python, type-checked in CI on every commit. These checks are handled through [`pre-commit`](https://github.com/pre-commit/pre-commit). First, install `pre-commit` through `pip`:

`pip install pre-commit`

`pre-commit` can be configured as a `git` hook, which will cause all style/type-checks to be run on commit. This is the recommended mode to use `pre-commit` in, as it will reduce the chance of CI failures due to incorrectly formatted code and/or type-checking failures. To configure this, run `pre-commit install` in the root of the repository.

Alternatively, you can run the checks manually at any time with `pre-commit run --all-files`.

## Automated testing

Note, this section summarizes the testing philosophy of the randomizer and gives a brief overview of the testing infrastructure. For information on how to write or run these tests, see `tests/README.md`.

Several automated tests exist to verify the correctness and exercise various parts of the randomizer. They are written in Python using the `pytest`
testing framework and are located in the `tests/` directory.

There are two distinct classes of automated tests used to test the randomizer.

1. General unit/integration-style tests that test parts of the randomizer application code like the shuffler, patcher, and UI.

2. Tests that spin up a live instance of the DeSmuME emulator that actually runs a copy of the ROM that has been patched in some way by the randomizer, while issuing commands to it and making assertions about the state of RAM and/or CPU registers. These are mostly used to test the base ROM patches, since realistically the only way to test those is to apply them to a real ROM and run it to make sure it behaves as expected.

Generally, the former type of test is easy to write and very cheap in the sense that, when done right, they have a low maintenance burden while providing a high value in terms of catching bugs. It's usually a good idea to have at least one of these tests if adding a new feature to the randomizer.

The latter type of test tends to be the opposite, in that they are usually difficult to write and can introduce a significant maintenance burden. You're essentially giving an emulator a series of buttons and touch screen coordinates to hit and then making assertions about the state of the game's memory based on them, which doesn't translate into easily readable code. Tests of this kind should probably be kept to a minimum, and only written for crucial components of the randomizer that cannot be tested with the former, more conventional approach (such as the base ROM patches). In any case, it's best to discuss with the randomizer team before writing one.
