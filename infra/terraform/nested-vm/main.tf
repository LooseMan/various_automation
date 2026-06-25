# 本ファイルは単一のLibvirtVMを直値指定で作成するもの

terraform {
  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.8.1"
    }
  }
}

# プロバイダーの接続先に、先ほど作ったAlmaLinux 10のIPアドレスをSSH経由で指定
provider "libvirt" {
  # 修正前が "qemu+ssh://192.168.56.5/system" のようになっている場合、
  # 接続先ホストの特権ユーザー（rootなど）を明示します。
  uri = "qemu+ssh://user@192.168.56.5/system"
}

# 孫VMのストレージプール定義
resource "libvirt_pool" "alma10_pool" {
  name = "guest-pool"
  type = "dir"
  # target ブロックの中に path を入れます
  target {
    path = "/var/lib/libvirt/images/pool"
  }
}

# 孫VM用のイメージ（AlmaLinux 10の内部ストレージにダウンロードされる）
resource "libvirt_volume" "guest_image" {
  # 下記名称でpoolに保存される
  name   = "alma9-guest-image.qcow2"
  pool   = libvirt_pool.alma10_pool.name
  format = "qcow2"

  # 最新のAlmaLinux 9 Generic Cloudイメージを指定
  source = "https://repo.almalinux.org/almalinux/9/cloud/x86_64/images/AlmaLinux-9-GenericCloud-latest.x86_64.qcow2"
}

# 孫VM用のネットワーク（ホストオンリー）
resource "libvirt_network" "host_only" {
  name      = "host-only-bridge"
  mode      = "none"                       # 外部通信なし
  addresses = ["192.168.150.0/24"]

  dns { enabled = false }                  # DNSサーバー無効
  dhcp { enabled = true }                  # DHCPサーバー有効
}

# 2. 調査用の最小限のcloud-init（_disk が正しいリソース名です）
resource "libvirt_cloudinit_disk" "commoninit" {
  name      = "commoninit.iso"
  user_data = <<EOF
#cloud-config
hostname: nested-guest-vm
manage_etc_hosts: true
user: almalinux
password: Password123!
chpasswd: { expire: False }
ssh_pwauth: True
EOF
}

# 孫VM本体の作成
resource "libvirt_domain" "nested_guest" {
  name   = "nested-guest-vm"
  memory = "2048"
  vcpu   = 2
  # MacOS 15以降だとkvmが使用できない？ためqemu
  type   = "qemu"
  # 🌟 ホストの物理CPUの命令セットをそのまま引き継ぐ（カーネルパニック対策、qemu64ではカーネルパニックになった）
  cpu {
    mode = "host-model"
  }
  # 本指定により、ディスクドライブにcommoninit.isoが挿入された状態でOSが起動→初期設定が実行される（3分くらいかかった）
  cloudinit = libvirt_cloudinit_disk.commoninit.id

  network_interface {
#    network_name = "default" # libvirt標準のNAT
    network_name = libvirt_network.host_only.name
    # .1はホストのブリッジのIPアドレスとして使われるため、2以降を指定する必要がある
    addresses      = ["192.168.150.10"]
#    wait_for_lease = false # DHCPがないため、リースの待ち受けをスキップ
    mac          = "52:54:00:15:00:10"
    wait_for_lease = true
  }

  disk {
    volume_id = libvirt_volume.guest_image.id
  }

  # Alma9以降はデフォルトのspice使えないためvnc
  graphics {
    type        = "vnc"
    listen_type = "address"
    listen_address = "0.0.0.0" # ホスト外部からもVNC接続を許可する場合。ホスト内限定なら "127.0.0.1"
    autoport    = true         # 空いているVNCポート（5900番以降）を自動割り当て
  }

  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }
}
