# Phantom Hourglass Randomizer Developer Documentation

This document provides a general overview of the parts of the randomizer, as well as a brief description of the file structure of the git repo.

Developers who wish to contribute to the randomizer should start here to get a high-level understanding of how the randomizer works, and then
proceed to `CONTRIBUTING.md` for a lower-level description for how to contribute code.

## Randomizer Architecture
There are 4 inter-operating components to the randomizer that work together to go from an unmodified, vanilla ROM to a logic-compliant randomized ROM.

### Base ROM patches
This refers to a collection of code changes and hooks that modify the behavior of the game, prior to any randomization even happening.
This is necessary to support aspects of the randomizer that aren't possible in the original game. For example, it is not possible to
have the sword sold in a shop in the original game; this is because the shop has a hardcoded list of items that it can hold. So, we
have a base patch that modifies the ROM's code to support this.
Another example is progressive swords; in the original game, there are two distinct sword items - the Oshus Sword and the Phantom Sword.
Randomizing these items in the vanilla ROM would mean the player can potentially find them in the wrong order. To fix this, most randomizers
implement progressive swords, where there is only a single sword item that always gives you the "next one up". This is yet another base patch.

These patches consist of, for the most part, code hooks written in either ARM assembly or C. In order to apply them to a ROM several steps must be taken
(TODO: outline these steps. For now, anyone interested can look at the Dockerfile), some of which require installing various development
dependencies. To avoid requiring users to install all of these just to run the randomizer, the base patches are pre-generated at compile-time and
bundled with the randomizer as BPS patches, which are in turn applied to users' ROMs by the patcher at run-time (see Patcher section for more info).

### UI
The user interface (UI) is the component of the randomizer that the user sees and interacts with directly, and is responsible for calling the other components of the randomizer.
It provides an interface that lets the user choose the settings they want for the randomizer and to provide their copy of the ROM; after the user provides these, the UI passes this information to the shuffler. It then takes the output of the shuffler and passes it to the patcher, which itself outputs the randomized ROM.
Note, "the UI" can potentially refer to _any_ user-facing interface to the randomizer; in the early stages of development, this will simply
be a CLI. Once the randomizer matures and is ready for general use, a GUI will be written to make it more convenient and user-friendly.

### Shuffler
The shuffler is the component of the randomizer that performs the high-level randomization of the game's items. As input, it takes logic files, aux data files,
and any settings relevant to randomization that the user specified and were passed by the UI. It parses the logic into a graph data structure and reads the aux data
files to determine what items are available to be shuffled. It then uses the logic and aux data together to randomly shuffle the items in the game such that it is still
completable, adhering to user settings where applicable. The final output of the shuffler is a new set of aux data with the items shuffled.

### Patcher
The patcher is the component of the randomizer that actually changes around the items in the game ROM. To put it simply, it takes in some set of aux data and outputs
a patched ROM with the items randomized as specified in the aux data. Generally, what will happen is the UI will call the shuffler and pass its output (the
randomized aux data) to the patcher.

## Structure of git repo
TODO
