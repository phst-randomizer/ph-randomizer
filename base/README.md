# Base ROM patch

This directory contains code to patch a ROM into an "open" state prior to randomization. For convenience, a Dockerfile is provided that contains all of the needed dependencies and commands. To build the patched version of the ROM:

1) Install Docker
2) Place your Legend of Zelda: Phantom Hourglass ROM (US version) inside the current directory (i.e. the one this README is located in)
3) Run the following command from the current directory (same directory as step 2)):
```
DOCKER_BUILDKIT=1 docker build --build-arg PH_ROM_PATH=in.nds -o out .
```
Note: replace `in.nds` with the path to your unpatched rom

4) The patched rom can now be found in the `out/` directory.
