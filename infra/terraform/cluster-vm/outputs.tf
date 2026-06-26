# 本ファイルは複数のLibvirtVMをクラスタ単位で作成するもの
# variablesでは外部から参照可能な設定(Terraformの出力)を定義する

output "cluster_type" {
  value = local.cluster.type
}

output "cluster_vms" {
  value = {
    for name, vm in local.vm_map : name => {
      group  = vm.group_name
      cpu    = vm.cpu
      memory = vm.memory
      ip     = vm.address
      mac    = vm.mac
    }
  }
}
