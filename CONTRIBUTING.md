# Contributing to the randomizer

## Local development environment

Before proceeding further in this document, you will need to set up a development environment. All required dependencies and tools will be preinstalled into this containerized environment for you.

1. Install [Visual Studio Code](https://code.visualstudio.com/)
1. Follow [VSCode Dev Container setup](https://code.visualstudio.com/docs/devcontainers/containers#_installation), if needed
1. Clone this git repository and open it in VSCode
1. From VSCode, press Ctrl-Shift-p and run `Dev Containers: Reopen in Container`
1. Now inside the container, run `uv run ph_rando` (or `uv run ph_rando --no-gui` for CLI-only mode). Alternatively, to run the shuffler or patcher in isolation, run `uv run ph_rando_shuffler` or `uv run ph_rando_patcher`.

## Code style/formatting guidelines

All code is linted in CI on every commit. These checks are handled through [`pre-commit`](https://github.com/pre-commit/pre-commit).

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
