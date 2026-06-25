# Cluster VM Terraform

`inventory.yml` を読み込み、選択したクラスタ定義から libvirt VM を作成します。

デフォルトの `cluster_name` は `test01` です。`inventory.yml` 上では `test01` が `small` なので、そのまま実行すると以下の4台を作成します。

- `test01-linux-01`
- `test01-linux-02`
- `test01-mac-01`
- `test01-win-01`

## Usage

```sh
terraform init
terraform plan
terraform apply
```

別クラスタを選ぶ場合:

```sh
terraform plan -var='cluster_name=test02'
terraform apply -var='cluster_name=test02'
```

libvirt 接続先を変える場合:

```sh
terraform plan -var='libvirt_uri=qemu+ssh://root@192.168.56.5/system'
```

## Notes

- VM の CPU とメモリは `inventory.yml` の `group_types` から取得します。
- VM 台数は `inventory.yml` の `cluster_types` から取得します。
- IP は `network_cidr` の `.10` から順番に割り当てます。
- デフォルトでは `192.168.150.0/24` の host-only network を作成します。
