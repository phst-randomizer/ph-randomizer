FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Don't write .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Don't buffer output
ENV PYTHONUNBUFFERED=1

# Configure uv for dev container
ENV UV_PROJECT_ENVIRONMENT=/home/vscode/uv-env \
    UV_CACHE_DIR=/home/vscode/uv/cache \
    UV_PYTHON_INSTALL_DIR=/home/vscode/uv/bin \
    UV_LINK_MODE=symlink

# Install runtime dependencies needed for development on various parts of the project
RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        git \
        gitk \
        graphviz \
        graphviz-dev \
        libx11-6 \
        libsdl2-2.0-0 \
        libsdl2-dev \
        libgtk2.0-0 \
        libgtk2.0-dev \
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
