# Download and compile ARMIPS
FROM python:3.12 AS compile_armips
RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        cmake && \
    rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --recurse-submodules https://github.com/Kingcom/armips.git
WORKDIR /armips
RUN cmake .
RUN make

# Download and compile Floating IPS patcher
FROM python:3.12 AS compile_flips
RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        git \
        g++ \
        build-essential \
        libgtk-3-dev \
        pkg-config && \
    rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/Alcaro/Flips.git
RUN chmod +x Flips/make-linux.sh
RUN cd Flips && ./make-linux.sh

FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04
# Don't write .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Don't buffer output
ENV PYTHONUNBUFFERED=1
# Install runtime dependencies needed for development on various parts of the project
RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        git \
        gitk \
        graphviz \
        graphviz-dev \
        gcc \
        gcc-arm-none-eabi \
        libx11-6 \
        libsdl2-2.0-0 \
        libsdl2-dev \
        libgtk2.0-0 \
        libgtk2.0-dev \
        libgtk-3-dev \
        libpcap0.8 \
        libpcap-dev \
        libosmesa6 \
        libglu1-mesa \
        x11-apps \
        libxcb-cursor0 \
        pulseaudio && \
    rm -rf /var/lib/apt/lists/*
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Set up user directories for vscode
USER vscode
RUN mkdir -p /home/vscode/.vscode-runtime
RUN mkdir -p /home/vscode/uv
WORKDIR /home/vscode/ph-randomizer
# Set up pre-commit cache directory so that it can be reused as a docker volume
RUN mkdir -p /home/vscode/.cache/pre-commit
RUN chown -R vscode /home/vscode/.cache/pre-commit

# Copy compiled armips and flips binaries from previous stages
COPY --from=compile_armips /armips/armips /bin/
COPY --from=compile_flips /Flips/flips /bin/
