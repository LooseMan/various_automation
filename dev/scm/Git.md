# Git with VSCode

## 前提条件

以降の手順は以下を前提に記述しています。

- ホストにVSCodeがインストール済みであること

## Gitサーバ側手順

### デバッグ用モジュールをビルド

### デバッグ用モジュールを実行

## VSCode側手順

### デバッグ用拡張を追加

サイドメニューから「拡張機能」を選択し、以下を追加する。

- [GitLens — Git supercharged](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens
)
- [Git Graph](https://marketplace.visualstudio.com/items?itemName=mhutchie.git-graph
)

### デバッグ対象アプリにアタッチ

## トラブルシューティング

### ・誤ってコミット・プッシュしてしまった場合

#### 1. ローカル側の取り消し

ターミナル上で`% git rebase -i HEAD~<遡りたいコミット数>`を実行する。
GitLens拡張を追加していると「Interactive Rebase」タブが開くので、取り消したいコミットで「drop」を選択する。
画面右下の「Start Rebase」をクリックすると、取り消しが実行される。

#### 2. リモート側の取り消し

ターミナル上で`% git push --force`を実行する。
コミットがリモートの履歴を書き換える場合、--forceの指定が必要。
