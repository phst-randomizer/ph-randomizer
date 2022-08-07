# Download and compile ARMIPS
FROM rikorose/gcc-cmake:gcc-8 AS compile_armips
RUN git clone --recurse-submodules https://github.com/Kingcom/armips.git
WORKDIR /armips
RUN cmake .
RUN make

# Download and compile ndstool
FROM ubuntu:20.04 AS compile_ndstool
RUN apt-get update && apt-get install -y build-essential git gcc g++ autotools-dev autoconf
RUN git clone https://github.com/devkitPro/ndstool
WORKDIR /ndstool
RUN aclocal && autoconf && automake --add-missing && chmod +x ./configure &&\
    ./configure --disable-dependency-tracking && make

# Download and compile Floating IPS patcher
FROM ubuntu:20.04 as compile_flips
RUN apt-get update && apt-get install -y git g++ build-essential
RUN git clone https://github.com/Alcaro/Flips.git
RUN chmod +x Flips/make.sh
RUN cd Flips && ./make.sh

FROM devkitpro/devkitarm:latest as build
WORKDIR /app
# Copy compiled armips, ndstool, and flips binaries from previous stages
COPY --from=compile_armips /armips/armips /app
COPY --from=compile_ndstool /ndstool/ndstool /app
COPY --from=compile_flips /Flips/flips /app
# Install gcc + software-properties-common (the latter so we can use `apt-add-repository`)
RUN apt-get update && apt-get install -y gcc software-properties-common
# Download fixy9 utility for updating y9.bin after making changes to overlays
RUN wget -O fixy9.exe https://github.com/StraDaMa/Legend-of-Zelda-Phantom-Hourglass-D-Pad-Patch/raw/master/fixy9.exe
# Install wine
RUN dpkg --add-architecture i386
RUN wget -qO - https://dl.winehq.org/wine-builds/winehq.key | apt-key add -
RUN apt-add-repository https://dl.winehq.org/wine-builds/debian/
RUN apt-get update && apt-get install -y winehq-stable
# Install python dependencies
RUN apt-get install -y python3-pip python3-pil
RUN pip3 install click ndspy==4.0.0
# Add needed source files to the docker build
ADD misc/* /app/
ADD src/* /app/src/
ADD Makefile /app
# Create base patch
ARG PH_ROM_PATH
ARG VERSION_STRING
ADD $PH_ROM_PATH /app
RUN make

# Export base patch to host
FROM scratch
COPY --from=build /app/patch.bps /
