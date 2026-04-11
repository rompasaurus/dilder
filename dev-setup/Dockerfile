FROM ubuntu:24.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install the ARM cross-compilation toolchain and build tools
RUN apt-get update && apt-get install -y \
    gcc-arm-none-eabi \
    libnewlib-arm-none-eabi \
    libstdc++-arm-none-eabi-newlib \
    cmake \
    ninja-build \
    python3 \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Clone the Pico SDK into the container
RUN git clone --recurse-submodules --depth 1 \
    https://github.com/raspberrypi/pico-sdk.git /opt/pico-sdk

ENV PICO_SDK_PATH=/opt/pico-sdk

WORKDIR /project

# Default command: configure + build
CMD ["sh", "-c", "mkdir -p build && cd build && cmake -G Ninja -DPICO_BOARD=pico_w .. && ninja"]
