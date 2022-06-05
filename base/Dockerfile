FROM rikorose/gcc-cmake:gcc-8 AS compile_armips
RUN git clone --recurse-submodules https://github.com/Kingcom/armips.git
WORKDIR /armips
RUN cmake .
RUN make

FROM ubuntu:20.04 AS compile_ndstool
RUN apt-get update && apt-get install -y build-essential git gcc g++ autotools-dev autoconf
RUN git clone https://github.com/devkitPro/ndstool
WORKDIR /ndstool
RUN aclocal && autoconf && automake --add-missing && chmod +x ./configure &&\
    ./configure --disable-dependency-tracking && make

FROM devkitpro/devkitarm:latest as build
WORKDIR /app
COPY --from=compile_armips /armips/armips /app
COPY --from=compile_ndstool /ndstool/ndstool /app
RUN apt-get update && apt-get install -y gcc software-properties-common
RUN git clone https://github.com/phst-randomizer/nds-compressors.git
RUN gcc nds-compressors/blz.c -o blz && chmod +x ./blz
RUN wget -O fixy9.exe https://github.com/StraDaMa/Legend-of-Zelda-Phantom-Hourglass-D-Pad-Patch/raw/master/fixy9.exe
RUN dpkg --add-architecture i386 
RUN wget -qO - https://dl.winehq.org/wine-builds/winehq.key | apt-key add -
RUN apt-add-repository https://dl.winehq.org/wine-builds/debian/
RUN apt-get update && apt-get install -y winehq-stable
# Install python dependencies
RUN apt-get install -y python3-pip python3-pil
RUN pip3 install click ndspy==4.0.0
ADD misc/* /app/
ADD src/* /app/src/
ADD Makefile /app
ARG PH_ROM_PATH
ARG VERSION_STRING
ADD $PH_ROM_PATH /app
RUN make

FROM scratch
COPY --from=build /app/out.nds /
