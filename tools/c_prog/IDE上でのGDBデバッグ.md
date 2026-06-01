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
