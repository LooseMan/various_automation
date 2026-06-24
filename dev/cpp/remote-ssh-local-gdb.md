# 構成イメージ（現実解）

あなたの制約を踏まえると、まず一番現実的なのはこれです。

```text id="wt2j5h"
Windows11
 └ VSCode

        ↓ Remote SSH

VirtualBox Alma9
 ├ vscode-server
 ├ gdb
 ├ cmake
 ├ gcc
 ├ source
 ├ build
 └ daemon
```

つまり:

* VSCode GUIだけWindows
* 開発実体はAlma9 VM
* Linuxネイティブgdb利用
* Remote SSHでIDE化

です。

これは:

* WSL不要
* Hyper-V不要
* オフライン対応可能
* daemon debug強い
* coverage相性良い

ので、かなり現実的。

---

# 要件まとめ

# Windows側

必要:

* Visual Studio Code
* Remote SSH extension
* C/C++ extension

推奨:

* Coverage Gutters
* CMake Tools
* GitLens

---

# Alma9側

必要:

```bash id="egjlwm"
gcc
g++
gdb
gdbserver
cmake
make
openssh-server
```

coverage使うなら:

```bash id="j3w15w"
gcovr
lcov
```

も推奨。

---

# ネットワーク

VirtualBox:

```text id="yctjlwm"
Host-Only Adapter
```

推奨。

例:

```text id="p9yivc"
Windows: 192.168.56.1
Alma9 : 192.168.56.10
```

---

# オフライン対応

重要。

---

# 事前取得するもの

## Alma9 RPM

オンライン環境で:

```bash id="a9rw86"
dnf download --resolve \
    gcc gcc-c++ gdb gdb-gdbserver \
    cmake make gcovr lcov openssh-server
```

---

# VSCode Server

オンラインLinuxで一度Remote SSH接続。

生成される:

```text id="e54jlwm"
~/.vscode-server
```

をtar化して持込。

---

# Alma9へ配置

```bash id="4fjlwm"
mkdir -p ~/.vscode-server
tar xzf vscode-server.tar.gz -C ~/
```

---

# Alma9初期設定

## SSH起動

```bash id="hjlwm3"
sudo systemctl enable sshd
sudo systemctl start sshd
```

---

# ファイアウォール

必要なら:

```bash id="jlwmg4"
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --reload
```

---

# VSCode接続

Windows側:

```text id="jlwm9n"
Remote SSH
  ↓
192.168.56.10
```

接続。

---

# ソース配置

Alma9側へ:

```text id="49jlwm"
/work/project
```

などに配置。

推奨:

```text id="jlwmx3"
~/work/project
```

---

# CMake coverage設定

## CMakeLists.txt

```cmake id="jlwm27"
option(ENABLE_COVERAGE "Enable coverage" OFF)

if(ENABLE_COVERAGE)
    add_compile_options(
        -O0
        -g3
        --coverage
        -fno-inline
        -fno-omit-frame-pointer
    )

    add_link_options(--coverage)
endif()
```

---

# ビルド

```bash id="jlwm0s"
cmake -B build -DENABLE_COVERAGE=ON
cmake --build build
```

---

# VSCodeデバッグ

## launch.json

```json id="jlwm7k"
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Attach daemon",
            "type": "cppdbg",
            "request": "attach",

            "program": "${workspaceFolder}/build/mydaemon",

            "processId": "${command:pickProcess}",

            "MIMode": "gdb",
            "miDebuggerPath": "/usr/bin/gdb",

            "cwd": "${workspaceFolder}"
        }
    ]
}
```

---

# デーモン起動

推奨:

```bash id="jlwm2e"
./mydaemon --foreground
```

または:

```ini id="jlwmkl"
Type=simple
```

でsystemd foreground化。

---

# coverage収集

## テスト後

```bash id="jlwmq5"
gcovr \
  -r . \
  build \
  --lcov \
  -o build/coverage.info
```

---

# VSCode設定

## settings.json

```json id="jlwm1p"
{
    "coverage-gutters.lcovname": "build/coverage.info"
}
```

---

# 実現できること

この構成で:

* VSCodeブレークポイント
* ステップ実行
* 変数確認
* daemon attach
* coverage可視化
* CMake build
* CTest
* simulator連携

が全部可能。

---

# あなたの案件とかなり相性が良い点

特に:

```text id="qlwjlwm"
Linux daemon
通信処理
Python simulator
coverage
RE環境
```

の組み合わせは、
この構成がかなり強い。

---

# 将来的な拡張

このまま発展させると:

```text id="jlwmzs"
GitLab CI
 ├ coverage
 ├ unit test
 ├ simulator test
 └ artifact
```

にも綺麗に繋がる。

かなりモダンなレガシー改善環境になります。
