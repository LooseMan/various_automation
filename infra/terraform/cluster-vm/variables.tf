# 本ファイルは複数のLibvirtVMをクラスタ単位で作成するもの
# variablesでは外部から指定可能な設定(Terraformの入力)を定義する

variable "libvirt_uri" {
  description = "libvirt connection URI"
  type        = string
  default     = "qemu+ssh://user@192.168.56.5/system"
}

variable "cluster_name" {
  description = "Cluster name from inventory.yml"
  type        = string
  default     = "test01"
}

variable "network_cidr" {
  description = "Host-only network CIDR for cluster VMs"
  type        = string
  default     = "192.168.150.0/24"
}

variable "ip_start_host" {
  description = "First host number used by cluster VMs. Host .1 is reserved by libvirt."
  type        = number
  default     = 10
}

variable "ssh_user" {
  description = "Initial user created by cloud-init"
  type        = string
  default     = "almalinux"
}

variable "ssh_password" {
  description = "Initial password created by cloud-init"
  type        = string
  default     = "Password123!"
  sensitive   = true
}
