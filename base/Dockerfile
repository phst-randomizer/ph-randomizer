FROM devkitpro/devkitarm:latest
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key|sudo apt-key add -
RUN echo 'deb http://apt.llvm.org/buster/ llvm-toolchain-buster-12 main' | sudo tee -a /etc/apt/sources.list
RUN echo 'deb-src http://apt.llvm.org/buster/ llvm-toolchain-buster-12 main' | sudo tee -a /etc/apt/sources.list
RUN sudo apt-get update
RUN sudo apt-get install -y clang-format-12
