Intel Macをお使いであれば、Apple SiliconのようなCPUエミュレーションのバグを心配する必要がありません。ネイティブの「x86_64」アーキテクチャとして非常に安定した環境でGDBデバッグが実行できます。
Intel MacにDocker環境を構築する手順は以下の通りです。
------------------------------
## macOS (Intel) への Docker インストール手順
Intel Macでは、GUIで直感的に操作できる公式の 「Docker Desktop for Mac」 をインストールするのが最も簡単で確実です。
## 1. インストーラーのダウンロード

   1. Docker公式サイトの Docker Desktop for Mac ダウンロードページ にアクセスします。
   2. ダウンロードボタンの選択肢から、必ず 「Mac with Intel chip」 を選択して .dmg ファイルをダウンロードしてください。

## 2. インストールと初期設定

   1. ダウンロードした .dmg ファイルをダブルクリックして開きます。
   2. 画面の指示に従い、Dockerアイコンを「Applications（アプリケーション）」フォルダへドラッグ＆ドロップします。
   3. アプリケーションフォルダから「Docker」を起動します。
   4. 初回起動時に「特権アクセス（Privileged Access）」を求められるので、Macのパスワードを入力して許可します。
   5. 利用規約（Service Agreement）を確認し、「Accept（同意）」をクリックします。

sudo ln -s /Applications/Docker.app/Contents/Resources/bin/docker /usr/local/bin/docker

## 3. 起動の確認
Macの画面右上（メニューバー）にクジラのアイコンが表示され、アイコン内のアニメーションが静止（緑色のステータスに変化）すれば起動完了です。
ターミナル（Terminal.app）を開き、以下のコマンドを実行してバージョンが表示されるか確認してください。

docker --version

------------------------------
## AlmaLinux 9 環境を立ち上げる最短手順
Dockerの準備ができたら、前述のAlmaLinux 9環境をすぐに試せます。Macのターミナルで以下のコマンドを順番に実行してください。

# 1. 適当な作業ディレクトリを作って移動
mkdir -p ~/almalinux-gdb && cd ~/almalinux-gdb
# 2. 前述の Dockerfile を作成 (cat コマンドで一気に書き込みます)
```zsh
cat << 'EOF' > Dockerfile
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
EOF
```
# 3. コンテナイメージをビルド (少し時間がかかります)
docker build -t alma9-gdb-env .

~/.docker/config.json
→"credsStore": "desktop"のdesktopを削除する！

ビルド時間は pkgインストールに124  + 秒、408パッケージ(1.1GB)入る
almalinux-gdb % docker image list    
                                                      i Info →   U  In Use
IMAGE                  ID             DISK USAGE   CONTENT SIZE   EXTRA
alma9-gdb-env:latest   829be915ec97       1.66GB          373MB        
almalinux-gdb % 

# 4. コンテナを起動 (GDB用の権限付き、カレントディレクトリをマウント)
docker run --rm -it \
  --cap-add=SYS_PTRACE \
  --security-opt="seccomp=unconfined" \
  -v $(pwd):/workspace \
  alma9-gdb-env
↓
[root@17f4194cdfd5 workspace]# uname -a
Linux 17f4194cdfd5 6.12.54-linuxkit #1 SMP PREEMPT_DYNAMIC Tue Nov  4 21:39:03 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
[root@17f4194cdfd5 workspace]# 

これでコンテナ内のターミナル（[root@... /workspace]#）に入ることができます。
Mac側の ~/almalinux-gdb フォルダに置いたC/C++ファイルやGDBスクリプトが、そのままコンテナ内の /workspace に同期されるため、すぐにビルドと検証を始められます。

