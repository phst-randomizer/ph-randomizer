# Download and compile ARMIPS
FROM python:3.12 AS compile_armips
RUN apt-get update && apt-get install -y cmake
RUN git clone --depth 1 --recurse-submodules https://github.com/Kingcom/armips.git
WORKDIR /armips
RUN cmake .
RUN make

# Download and compile Floating IPS patcher
FROM python:3.12 as compile_flips
RUN apt-get update && apt-get install -y git g++ build-essential libgtk-3-dev pkg-config
RUN git clone --depth 1 https://github.com/Alcaro/Flips.git
RUN chmod +x Flips/make-linux.sh
RUN cd Flips && ./make-linux.sh

# Build base patch
FROM python:3.12 as build
WORKDIR /app
# Copy compiled armips, and flips binaries from previous stages
COPY --from=compile_armips /armips/armips /app
COPY --from=compile_flips /Flips/flips /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    gcc-arm-none-eabi
# Needed for `flips` patcher
RUN apt-get install -y libgtk-3-dev
# Install python dependencies
ADD requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# Add needed source files to the docker build
ADD data/* /app/
ADD code/* /app/code/
ADD fix_y9.py /app
ADD extract_rom.py /app
ADD rebuild_rom.py /app
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
