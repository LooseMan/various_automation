# 全体アーキテクチャ

   1. Mac (ホスト): vbox プロバイダーを使用してAlmaLinux 10のVMを作成。
   2. AlmaLinux 10 (中間のVM): libvirtを起動し、ホスト（Mac）からのリモート接続を許可。
   3. Mac (ホスト): libvirt プロバイダーを使って、AlmaLinux 10上のハイパーバイザへSSH経由でアクセスし、孫VMを作成。

---

## Step1. terraform のインストール

brewリポジトリにhashicorpリポジトリを追加

```zsh
~ % brew tap hashicorp/tap

==> Tapping hashicorp/tap
Cloning into '/usr/local/Homebrew/Library/Taps/hashicorp/homebrew-tap'...
remote: Enumerating objects: 6723, done.
remote: Counting objects: 100% (1056/1056), done.
remote: Compressing objects: 100% (316/316), done.
remote: Total 6723 (delta 918), reused 746 (delta 740), pack-reused 5667 (from 4)
Receiving objects: 100% (6723/6723), 1.20 MiB | 3.10 MiB/s, done.
Resolving deltas: 100% (4851/4851), done.
Tapped 2 casks and 32 formulae (100 files, 1.7MB).
```

hashicorpリポジトリからterraformをインストール

```zsh
~ % brew install terraform
✔︎ JSON API formula.jws.json                                                                             Downloaded   33.2MB/ 33.2MB
✔︎ JSON API cask.jws.json                                                                                Downloaded   16.9MB/ 16.9MB
Inspect the formula dependency plan before installing with `brew install --ask`.
Enable ask mode by setting `HOMEBREW_ASK=1`.
Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
==> Fetching downloads for: terraform
✔︎ Formula terraform (1.15.5)                                                                            Verified     36.5MB/ 36.5MB
==> Installing terraform from hashicorp/tap
Error: Your Command Line Tools are too outdated.
Update them from Software Update in System Settings.

If that doesn't show you any updates, run:
  sudo rm -rf /Library/Developer/CommandLineTools
  sudo xcode-select --install

Alternatively, manually download them from:
  https://developer.apple.com/download/all/.
You should download the Command Line Tools for Xcode 26.3.
```

MacOSでCOmmandLineToolsが古いと上記エラーが発生する。

---

ホストオンリーNW経由でVMにSSH接続
※NATの場合ホストがVMを認識できないためSSH接続できない

1. VM上でIPアドレス割り当てを確認

```bash
user@localhost:~$ ip addr
...
3: enp0s8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 08:00:27:84:d5:1f brd ff:ff:ff:ff:ff:ff
    altname enx08002784d51f
    inet 192.168.56.5/24 brd 192.168.56.255 scope global noprefixroute enp0s8
       valid_lft forever preferred_lft forever
user@localhost:~$ 
```

2.VMにSSH接続

```zsh
various_automation % ssh user@192.168.56.5
Web console: https://localhost:9090/ or https://10.0.2.15:9090/

Last login: Wed Jun  3 20:27:29 2026
user@localhost:~$ 
```

---

## Step 2: AlmaLinux 10 内での libvirt（KVM）設定

AlmaLinux 10が起動したら、内部に入ってKVMと、外部（Mac）から接続を待ち受けるための設定を行います。

```bash
$ sudo dnf groupinstall "Virtualization Host" -y
$ sudo dnf install libvirt-daemon-kvm qemu-kvm virt-install -y

$ sudo systemctl enable --now libvirtd
Created symlink '/etc/systemd/system/multi-user.target.wants/libvirtd.service' → '/usr/lib/systemd/system/libvirtd.service'.
Created symlink '/etc/systemd/system/sockets.target.wants/libvirtd.socket' → '/usr/lib/systemd/system/libvirtd.socket'.
Created symlink '/etc/systemd/system/sockets.target.wants/libvirtd-ro.socket' → '/usr/lib/systemd/system/libvirtd-ro.socket'.
Created symlink '/etc/systemd/system/sockets.target.wants/libvirtd-admin.socket' → '/usr/lib/systemd/system/libvirtd-admin.socket'.
```

※デフォルトでlibvirtdサービスは無効化されている。

```bash
user@localhost:~$ systemctl status libvirtd
○ libvirtd.service - libvirt legacy monolithic daemon
     Loaded: loaded (/usr/lib/systemd/system/libvirtd.service; disabled; preset: disabled)
     Active: inactive (dead)
TriggeredBy: ○ libvirtd-admin.socket
             ○ libvirtd-ro.socket
             ○ libvirtd.socket
       Docs: man:libvirtd(8)
             https://libvirt.org/
user@localhost:~$ 
```

### トラブル1: libvirtdサービスの開始に失敗する

VMの

```bash
 6月 03 20:43:58 localhost.localdomain dnsmasq-dhcp[4414]: read /var/lib/libvirt/dnsmasq/default.hostsfile
 6月 03 20:43:58 localhost.localdomain libvirtd[5258]: libvirt version: 11.10.0, package: 12.el10_2.alma.1 (AlmaLinux Packaging Team <packager@almalin>
 6月 03 20:43:58 localhost.localdomain libvirtd[5258]: hostname: localhost.localdomain
 6月 03 20:43:58 localhost.localdomain libvirtd[5258]: /dev/kvm を開けません: そのようなファイルやディレクトリはありません
lines 1-26/26 (END)
```

 VirtualBoxであれば以下のコマンドでネスト仮想化を有効化できる。

```zsh
~ % VBoxManage modifyvm "AlmaLinux-10.1" --nested-hw-virt on        

~ % 
```

MacのTerraformからAlmaLinux 10のlibvirtを叩く際、一般的にはSSH経由で接続します。毎回パスワードを求められないよう、MacのSSH公開鍵をAlmaLinuxの ~/.ssh/authorized_keys に登録しておきます。

---

## Step 3: MacからAlmaLinux 10上に「孫VM」を作る（Terraform）

ここからが本題です。Mac側の別の作業ディレクトリ（例: nested-vm）で、AlmaLinux 10のlibvirtをターゲットにした Terraformファイルを作成します。
→ nested-vm/main.tf

これをMac側で terraform apply すると、指示がネットワークを越えてAlmaLinux 10に飛び、AlmaLinux 10の内部でKVMの孫VM（nested-guest-vm）が立ち上がります。

### トラブル：プロバイダが見つからない

`terraform apply`の実行前に、validateでの事前チェックを推奨する。

```zsh
nested-vm % terraform validate
╷
│ Error: Missing required provider
│ 
│ This configuration requires provider registry.terraform.io/dmacvicar/libvirt, but that provider isn't available. You may be able
│ to install it automatically by running:
│   terraform init
╵
nested-vm % 
```

→プロバイダの取得のため、`terraform init`を実行する。

```zsh
nested-vm % terraform init
Initializing provider plugins found in the configuration...
- Finding dmacvicar/libvirt versions matching "0.8.1"...
- Installing dmacvicar/libvirt v0.8.1...
- Installed dmacvicar/libvirt v0.8.1 (self-signed, key ID 0833E38C51E74D26)
Partner and community providers are signed by their developers.
If you'd like to know more about provider signing, you can read about it here:
https://developer.hashicorp.com/terraform/cli/plugins/signing

Initializing the backend...


Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
nested-vm % 
```

### トラブル：SSH接続に失敗する

```zsh
nested-vm % terraform apply
╷
│ Error: failed to connect: failed to connect to remote host '192.168.56.5': ssh: handshake failed: ssh: unable to authenticate, attempted methods [none publickey], no supported methods remain
│ 
│   with provider["registry.terraform.io/dmacvicar/libvirt"],
│   on main.tf line 11, in provider "libvirt":
│   11: provider "libvirt" {
│ 
╵
nested-vm % 
```

libvirt プロバイダーは内部のGo言語製SSHクライアントを使用する。
libvirt プロバイダーは、ssh-agent にロードされている鍵を自動的に利用するため、ターミナルで以下を実行し鍵を明示的にロードする。

```zsh
# ssh-agentをバックグラウンドで起動
eval "$(ssh-agent -s)"

# リモートホストにログインする際に使う秘密鍵を追加
# (使用する鍵に合わせ以下のファイル名を決定すること)
ssh-add ~/.ssh/id_ed25519

# 鍵が正しく登録されたか確認
ssh-add -l
```

## VM作成

```zsh
nested-vm % terraform apply          

Terraform used the selected providers to generate the following execution plan. Resource actions are
indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # libvirt_domain.nested_guest will be created
  + resource "libvirt_domain" "nested_guest" {
      + arch        = (known after apply)
      + autostart   = (known after apply)
      + emulator    = (known after apply)
      + fw_cfg_name = "opt/com.coreos/config"
      + id          = (known after apply)
      + machine     = (known after apply)
      + memory      = 2048
      + name        = "nested-guest-vm"
      + qemu_agent  = false
      + running     = true
      + type        = "kvm"
      + vcpu        = 2

      + console {
          + source_host    = "127.0.0.1"
          + source_service = "0"
          + target_port    = "0"
          + target_type    = "serial"
          + type           = "pty"
        }

      + cpu (known after apply)

      + disk {
          + scsi      = false
          + volume_id = (known after apply)
          + wwn       = (known after apply)
        }

      + network_interface {
          + addresses    = (known after apply)
          + hostname     = (known after apply)
          + mac          = (known after apply)
          + network_id   = (known after apply)
          + network_name = "default"
        }

      + nvram (known after apply)
    }

  # libvirt_pool.alma10_pool will be created
  + resource "libvirt_pool" "alma10_pool" {
      + allocation = (known after apply)
      + available  = (known after apply)
      + capacity   = (known after apply)
      + id         = (known after apply)
      + name       = "guest-pool"
      + type       = "dir"

      + target {
          + path = "/var/lib/libvirt/images/pool"
        }
    }

  # libvirt_volume.guest_image will be created
  + resource "libvirt_volume" "guest_image" {
      + format = "qcow2"
      + id     = (known after apply)
      + name   = "guest-os.qcow2"
      + pool   = "guest-pool"
      + size   = (known after apply)
      + source = "https://almalinux.org"
    }

Plan: 3 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

### トラブル：KVMを使用できない

```zsh
libvirt_domain.nested_guest: Creating...
╷
│ Error: error defining libvirt domain: サポートされない設定: エミュレーター '/usr/libexec/qemu-kvm' は virt タイプ 'kvm' をサポートしません
│ 
│   with libvirt_domain.nested_guest,
│   on main.tf line 39, in resource "libvirt_domain" "nested_guest":
│   39: resource "libvirt_domain" "nested_guest" {
│ 
╵
nested-vm % 
```

MacOS 15以降だとkvmが使用できない？ため kvm -> qemu に修正する。

```tf
resource "libvirt_domain" "nested_guest" {
  name   = "nested-guest-vm"
  memory = "2048"
  vcpu   = 2

  # MacOS 15以降だとkvmが使用できない？ためqemu
  type   = "qemu"
```

### トラブル：作成したVMをroot権限でしか確認できない

libvirtグループへの追加だけでは足りない。

```bash
sudo usermod -aG libvirt $USER
```

以下でポリシーキットルールを追加する。

```bash
$ sudo tee /etc/polkit-1/rules.d/50-libvirt.rules << 'EOF'
polkit.addRule(function(action, subject) {
    if (action.id == "org.libvirt.unix.manage" &&
        subject.isInGroup("libvirt")) {
        return polkit.Result.YES;
    }
});
EOF
```

それでもダメな場合、libvirtコマンドの参照先がユーザ領域を向いているため（デフォルトの動作）。
以下のコマンドでデフォルトをシステム領域に変更する。

```bash
echo "export LIBVIRT_DEFAULT_URI='qemu:///system'" >> ~/.bashrc
source ~/.bashrc
```

以上の対応によりlibvirtグループユーザがlibvirtコマンドを実行可能となる。

```bash
user@localhost:~$ virsh list --all
 Id   名前              状態
--------------------------------
 1    nested-guest-vm   実行中

user@localhost:~$ 
```

### トラブル：cloud-init用isoイメージの作成に失敗する

```zsh
libvirt_cloudinit_disk.commoninit: Creating...
╷
│ Error: error while starting the creation of CloudInit's ISO image: exec: "mkisofs": executable file not found in $PATH
│ 
│   with libvirt_cloudinit_disk.commoninit,
│   on main.tf line 49, in resource "libvirt_cloudinit_disk" "commoninit":
│   49: resource "libvirt_cloudinit_disk" "commoninit" {
│ 
╵ 
```

MacOSの場合、デフォルトでmkisofsは入らない。また、brewからmkisofsをインストールできないため、代わりにxorrisoをインストールし、mkisofsとして使用する。

```zsh

brew install xorriso
sudo ln -s $(which xorriso) /usr/local/bin/mkisofs

```

## ノウハウ

### 環境の再作成

```zsh

sudo virsh destroy nested-guest-vm   # すでに停止していればエラーになりますが無視してOKです
sudo virsh undefine nested-guest-vm  # 🌟 これで既存のUUIDが削除されます

terraform init
terraform apply

```

なお、cloud-init用のisoは`/var/lib/libvirt/images/commoninit.iso`としてlibvirtサーバ上に作成される。
