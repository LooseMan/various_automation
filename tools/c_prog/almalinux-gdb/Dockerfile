FROM almalinux:9

# 1. C/C++開発用パッケージ をインストール
RUN dnf -y update && \
    dnf -y install \
        gcc \
        gcc-c++ \
        gdb \
        make \
        git \
        tar \
        python3-pip \
        ncurses-devel \
        glibc-devel && \
    dnf clean all

# 2. pwndbg をインストール
WORKDIR /root
RUN curl --proto '=https' --tlsv1.2 -LsSf 'https://install.pwndbg.re' | sh -s -- -t pwndbg-gdb

WORKDIR /workspace
CMD ["/bin/bash"]
