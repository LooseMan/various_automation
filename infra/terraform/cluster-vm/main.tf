# 本ファイルは複数のLibvirtVMをクラスタ単位で作成するもの

terraform {
  required_version = ">= 1.3.0"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.8.1"
    }
  }
}

provider "libvirt" {
  uri = var.libvirt_uri
}

# localsはterraform変数で、外部から指定したいものはvariable化する
# variableはデフォルト値を設定でき、実行時引数などで上書き可能
# 環境の生成単位はホストのため、以下で
# ymlに定義されたクラスタ構成を「クラスタ->グループ->ホスト」の順で展開
locals {
  inventory = yamldecode(file("${path.module}/inventory.yml"))

  cluster      = local.inventory.clusters[var.cluster_name]
  cluster_type = local.inventory.cluster_types[local.cluster.type]

  vm_list = flatten([
    for group_name in sort(keys(local.cluster_type)) : [
      for n in range(local.cluster_type[group_name].count) : {
        name       = "${var.cluster_name}-${group_name}-${format("%02d", n + 1)}"
        group_name = group_name
        ordinal    = n + 1
        cpu        = local.inventory.group_types[group_name].cpu
        memory     = local.inventory.group_types[group_name].memory
      }
    ]
  ])

  vm_map = {
    for index, vm in local.vm_list : vm.name => merge(vm, {
      index   = index
      address = cidrhost(var.network_cidr, var.ip_start_host + index)
      mac     = format("52:54:00:15:%02x:%02x", floor((var.ip_start_host + index) / 256), (var.ip_start_host + index) % 256)
    })
  }
}

resource "libvirt_pool" "cluster_pool" {
  name = "cluster-pool"
  type = "dir"

  target {
    path = "/var/lib/libvirt/images/cluster-pool"
  }
}

resource "libvirt_volume" "base_image" {
  name   = "alma9-cluster-base.qcow2"
  pool   = libvirt_pool.cluster_pool.name
  format = "qcow2"
  source = "https://repo.almalinux.org/almalinux/9/cloud/x86_64/images/AlmaLinux-9-GenericCloud-latest.x86_64.qcow2"
}

resource "libvirt_volume" "vm_disk" {
  for_each       = local.vm_map
  name           = "${each.key}.qcow2"
  pool           = libvirt_pool.cluster_pool.name
  base_volume_id = libvirt_volume.base_image.id
  size           = 20 * 1024 * 1024 * 1024
}

resource "libvirt_network" "host_only" {
  name      = "${var.cluster_name}-host-only"
  mode      = "none"
  addresses = [var.network_cidr]

  dns {
    enabled = false
  }

  dhcp {
    enabled = true
  }
}

resource "libvirt_cloudinit_disk" "commoninit" {
  for_each = local.vm_map
  name     = "${each.key}-commoninit.iso"
  pool     = libvirt_pool.cluster_pool.name

  user_data = <<EOF
#cloud-config
hostname: ${each.key}
manage_etc_hosts: true
user: ${var.ssh_user}
password: ${var.ssh_password}
chpasswd: { expire: False }
ssh_pwauth: True
EOF
}

resource "libvirt_domain" "cluster_vm" {
  for_each = local.vm_map

  name   = each.key
  memory = each.value.memory
  vcpu   = each.value.cpu
  type   = "qemu"

  cpu {
    mode = "host-model"
  }

  cloudinit = libvirt_cloudinit_disk.commoninit[each.key].id

  network_interface {
    network_name   = libvirt_network.host_only.name
    addresses      = [each.value.address]
    mac            = each.value.mac
    wait_for_lease = true
  }

  disk {
    volume_id = libvirt_volume.vm_disk[each.key].id
  }

  graphics {
    type           = "vnc"
    listen_type    = "address"
    listen_address = "0.0.0.0"
    autoport       = true
  }

  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }
}
