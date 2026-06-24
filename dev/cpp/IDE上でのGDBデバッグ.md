# GDB Debug on IDE

IDE（統合開発環境）上でPythonをデバッグしたい人に捧ぐ。
筆者がVSCode使いのため、IDE側の手順はVSCode用です。

## 前提条件

以降の手順は以下を前提に記述しています。
- ホストにVSCodeがインストール済みであること
- ホストからリモートにSSH接続できること
- リモートにgdbおよびgdbserverがインストール済みであること

## C/C++側手順

### デバッグ用モジュールをビルド

以下のオプションを指定してモジュールをビルドする。

|オプション|説明
|-|-
|-g | デバッグ情報を追加
|-O0 | 最適化無効

```sh
# Cソースの場合の例
gcc -g -O0 function_server.c -o function_server
# Cppソースの場合の例
g++ -g -O0 function_server.cpp -o function_server_cpp
```

### デバッグ用モジュールを実行

IDEからgdbで直接プロセスにアタッチすると、アプリが異常停止したり、デバッグ機能が使用できない場合がある。そのため、アプリをgdbserver経由でアタッチ可能とし、IDEからgdbでgdbserverにアタッチする。アタッチ対象プロセスのPIDを事前に`pgrep`などで調べておくこと。

|オプション|説明
|-|-
|--attach :<ポート番号> | アタッチ要求待ちポート

```sh
# 実行例
gdbserver --attach :5678 123
```

## IDE側手順(VSCodeの場合)

### デバッグ用拡張を追加

サイドメニューから「拡張機能」を選択し。[C/C++](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cpptools
)を追加する。

### デバッグ対象アプリにアタッチ

以下のデバッグ構成をlaunch.jsonに追加する。

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "C++ gdbserver アタッチデバッグ",
      "type": "cppdbg",
      // gdbserver接続時は必ず "launch" にします
      "request": "launch",
      // ホストPC上にある、デバッグ情報付きバイナリのパス
      "program": "${workspaceFolder}/build/my_program",
      "MIMode": "gdb",
      "cwd": "${workspaceFolder}",
      // ターゲット機器の「IPアドレス:ポート番号」を指定
      "miDebuggerServerAddress": "192.168.1.100:1234",
      // ホストPC側で使用するGDBのパス
      "miDebuggerPath": "/usr/bin/aarch64-linux-gnu-gdb",
    }
  ]
}

```

request: "attach" にしてしまうと、VSCodeがローカルマシンのプロセスを探しにいってしまい、cwd がないなどの様々な不整合（警告）の原因になる。
ビルドに使用したSRCを"${workspaceFolder}"以下に配置しておくこと。

サイドメニューから「実行とデバッグ」を選択し。追加した「C/C++ デバッガー: リモートアタッチ」を開始する。IDE上でブレークポイントを設定し、関連処理を実行すると、設定箇所でブレークする。

### GDBコマンドを実行

### C++ STLのデバッグ表示の改善

C++のSTLコンテナ（std::vectorなど）をデバッグする際、デフォルトでは生（Raw）のメモリ構造が表示される。
デバッガにはSTLの内部構造をきれいに整形して表示する「Pretty Printer」(Python製)という機能が用意されている。
当該機能を有効化するため、launch.jsonに以下のsetupCommandsを追加する。

```json
{
  "setupCommands": [
      {
          "description": "GDB の Pretty-printing を連動有効化",
          "text": "-enable-pretty-printing",
          "ignoreFailures": true
      },
      {
          "description": "gdbserver接続時の自動ロード失敗を回避するため、手動でPretty-printerを読み込む",
          "text": "source /usr/share/gdb/auto-load/usr/lib64/libstdc++.so.6.0.32-gdb.py",
          "ignoreFailures": true
      }
  ]
}
```

「Pretty-printer」の読み込み先は環境依存である。リモートで以下のコマンドを実行し確認する。

```sh
ls /usr/share/gdb/auto-load/usr/lib64/libstdc++.so.*-gdb.py
```

ibstdc++.so.*-gdb.pyが存在しない場合、以下のコマンドでインストールする。

```sh
sudo dnf install gcc-gdb-plugin
```

また、「Pretty Printer」の読み込みはgdbserverを経由せずgdbで直接プロセスにアタッチする場合は不要である。詳細は以下を参照。
[The option -enable-pretty-printing doesn't work for remote debugging with gdbserver · Issue #4568 · microsoft/vscode-cpptools](https://github.com/microsoft/vscode-cpptools/issues/4568)

