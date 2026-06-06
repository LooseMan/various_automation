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


# 孫VM本体の作成
resource "libvirt_domain" "nested_guest" {
  name   = "nested-guest-vm"
  memory = "2048"
  vcpu   = 2

  # MacOS 15以降だとkvmが使用できない？ためqemu
  type   = "qemu"

  network_interface {
    network_name = "default" # libvirt標準のNAT
  }

  disk {
    volume_id = libvirt_volume.guest_image.id
  }

  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }
}
