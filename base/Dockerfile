# Download and compile ARMIPS
FROM rikorose/gcc-cmake:gcc-8 AS compile_armips
RUN git clone --recurse-submodules https://github.com/Kingcom/armips.git
WORKDIR /armips
RUN cmake .
RUN make

# Download and compile ndstool
FROM python:3.11 AS compile_ndstool
RUN apt-get update && apt-get install -y build-essential git gcc g++ autotools-dev autoconf
RUN git clone https://github.com/devkitPro/ndstool
WORKDIR /ndstool
RUN aclocal && autoconf && automake --add-missing && chmod +x ./configure &&\
    ./configure --disable-dependency-tracking && make

# Download and compile Floating IPS patcher
FROM python:3.11 as compile_flips
RUN apt-get update && apt-get install -y git g++ build-essential
RUN git clone https://github.com/Alcaro/Flips.git
RUN chmod +x Flips/make.sh
RUN cd Flips && ./make.sh

# Build base patch
FROM python:3.11 as build
WORKDIR /app
# Copy compiled armips, ndstool, and flips binaries from previous stages
COPY --from=compile_armips /armips/armips /app
COPY --from=compile_ndstool /ndstool/ndstool /app
COPY --from=compile_flips /Flips/flips /app
# Install gcc + software-properties-common (the latter so we can use `apt-add-repository`)
RUN apt-get update && apt-get install -y gcc software-properties-common
# Install ARM gcc toolchain
RUN apt-get install -y gcc-arm-none-eabi
# Download fixy9 utility for updating y9.bin after making changes to overlays
RUN wget -O fixy9.exe https://github.com/StraDaMa/Legend-of-Zelda-Phantom-Hourglass-D-Pad-Patch/raw/master/fixy9.exe
# Install wine
RUN dpkg --add-architecture i386
RUN wget -qO - https://dl.winehq.org/wine-builds/winehq.key | apt-key add -
RUN apt-add-repository https://dl.winehq.org/wine-builds/debian/
RUN apt-get update && apt-get install -y wine
# Install python dependencies
ADD requirements.txt /app/
RUN pip install -r requirements.txt
# Add needed source files to the docker build
ADD data/* /app/
ADD code/* /app/code/
ADD Makefile /app
# Create base patch
ARG PH_ROM_PATH
ARG VERSION_STRING
ADD $PH_ROM_PATH /app
RUN make
# Name base patch using its source ROM's SHA-256 so that we can tell what ROM it's for.
RUN export sha256=$(sha256sum $PH_ROM_PATH | awk '{ print $1 }'); mv patch.bps $sha256.bps

# Export base patch to host
FROM scratch
COPY --from=build /app/*.bps /
