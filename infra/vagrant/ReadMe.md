# 全体アーキテクチャ

## CentOS 5.11 環境構築

レガシー環境としてCent5のVirtualBoxVMをVagrantで作成する。

### VagrantBox取得

`bento/centos-5.11`をベースイメージに使用する。
最新版(202002.04.0)はVirtualBox版のみ提供されている。

```json
 "description": "Centos 5.11 Vagrant box created with Bento by Chef",
  "short_description": "Centos 5.11 Vagrant box created with Bento by Chef",
  "versions": [
    {
      "version": "202002.04.0",
      "status": "active",
      "description_html": "\u003Cp\u003ECentos 5.11 Vagrant box version 202002.04.0 created with Bento by Chef. Tool versions: virtualbox: 6.1.2, packer: 1.5.1\u003C/p\u003E\n",
      "description_markdown": "Centos 5.11 Vagrant box version 202002.04.0 created with Bento by Chef. Tool versions: virtualbox: 6.1.2, packer: 1.5.1",
      "providers": [
        {
          "name": "virtualbox",
          "architecture": "unknown",
          "default_architecture": true,
          "checksum": "",
          "checksum_type": "none",
          "url": "https://vagrantcloud.com/bento/boxes/centos-5.11/versions/202002.04.0/providers/virtualbox/unknown/vagrant.box"
        }
      ]
    },
```

Vagrantfile取得後、VMを作成する。

```zsh
% vagrant init bento/centos-5.11
% vagrant up
```

VMにはデフォルトでvagrant/vagrantでログインできる。

### SSH接続用IPアドレス取得

```bash
#!/bin/bash
VM_NAME="your-rhel5-vm-name" # Libvirt上のVM名

# LibvirtからIPアドレスを自動取得
VM_IP=$(virsh domifaddr "$VM_NAME" | grep -oE '192\.168\.[0-9]+\.[0-9]+' | head -n 1)

if [ -z "$VM_IP" ]; then
    echo "エラー: VMのIPアドレスを取得できませんでした。VMが起動しているか確認してください。"
    exit 1
fi

echo "VM IP: $VM_IP に対してAnsibleを実行します..."

# インベントリをインラインで指定して実行
ansible-playbook -i "$VM_IP," playbook.yml -u root --private-key=/path/to/id_rsa
```

### 初期設定（Ansible）

```yaml
---
- name: Vagrant-like Provisioning for RHEL5 via Raw Module
  hosts: all
  gather_facts: no  # RHEL5の古いPython対策で必須
  vars:
    # 構成に合わせて変更してください
    target_hostname: "rhel5-vm.local"
    static_ip: "192.168.122.150"
    gateway: "192.168.122.1"

  tasks:
    - name: 1. 永続的なホスト名の設定 (/etc/sysconfig/network の書き換え)
      raw: |
        # 既存のHOSTNAME行を削除し、新しいホスト名を追記
        sed -i '/^HOSTNAME=/d' /etc/sysconfig/network
        echo "HOSTNAME={{ target_hostname }}" >> /etc/sysconfig/network

    - name: 2. 現在のセッションへホスト名を即時反映
      raw: "hostname {{ target_hostname }}"

    - name: 3. /etc/hosts への自ホスト名登録 (名前解決のエラー防止)
      raw: |
        # 127.0.0.1 の行に新しいホスト名を追加
        sed -i 's/^127.0.0.1.*/127.0.0.1   localhost localhost.localdomain {{ target_hostname }}/' /etc/hosts

    - name: 4. 既存のdhclientプロセスを停止 (ネットワーク設定変更前の競合防止)
      raw: pkill dhclient || true

    - name: 5. ifcfg-eth0 をスタティック設定に書き換え
      raw: |
        cat << 'EOF' > /etc/sysconfig/network-scripts/ifcfg-eth0
        DEVICE=eth0
        BOOTPROTO=static
        IPADDR={{ static_ip }}
        NETMASK=255.255.255.0
        GATEWAY={{ gateway }}
        ONBOOT=yes
        TYPE=Ethernet
        EOF

    - name: 6. ネットワークサービスを再起動（SSH切断を考慮し非同期実行）
      raw: service network restart
      async: 15
      poll: 0

    - name: 7. 新しい固定IPへの切り替わりをローカルで待機
      delegate_to: localhost
      wait_for:
        host: "{{ static_ip }}"
        port: 22
        delay: 5
        timeout: 60

    - name: 8. 反映確認用のデバッグ (次のプレイブック実行時などに確認可能)
      raw: "uname -n && ip addr show eth0"
```
