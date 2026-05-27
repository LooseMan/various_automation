# Python Debug on IDE

IDE（統合開発環境）上でPythonをデバッグしたい人に捧ぐ。
筆者がVSCode使いのため、IDE側の手順はVSCode用です。

## 前提条件

以降の手順は以下を前提に記述しています。
- Python・VSCodeがインストール済みであること

## Python側手順

### デバッグ用モジュールを追加

以下のコマンドで「debugpy」モジュールを追加する。
```sh
$ pip install debugpy
```

### デバッグ対象スクリプトを実行

以下のオプションを指定してpyスクリプトを実行する。
|オプション|説明
|-|-
|-m debugpy | debugpyモジュール経由で実行
|--listen <ポート番号> | アタッチ要求待ちポート
|--wait-for-client | アタッチ要求を待機する

実行例:
```sh
$ python -m debugpy --listen 5678 --wait-for-client sample.py
```
※<デバッグするpyスクリプトのパスにASCIIコード以外が含まれるとdebugpyが正常に動作しないため注意

## IDE側手順(VSCodeの場合)

### デバッグ用拡張を追加

サイドメニューから「拡張機能」を選択し。[Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python
)を追加する。

### デバッグ対象スクリプトにアタッチ

以下のデバッグ構成をlaunch.jsonに追加する。
```json
{
	"name": "Python デバッガー: リモートアタッチ",
	"type": "debugpy",
	"request": "attach",
	"connect": {
		"host": "localhost",
		"port": 5678
	},
	"pathMappings": [
		{
			"localRoot": "${workspaceFolder}",
			"remoteRoot": "."
		}
	]
}
```

サイドメニューから「実行とデバッグ」を選択し。追加した「Python デバッガー: リモートアタッチ」を開始する。
