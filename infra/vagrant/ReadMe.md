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

LibvirtのDHCPリース情報を参照して動的にIPアドレスを取得し、Ansibleのインベントリに登録してプロビジョニングを行います。
RHEL 5（Red Hat Enterprise Linux 5）の仮想マシン（VM）が初期状態でDHCP設定（ONBOOT=yes）になっている場合、起動時にLibvirtの仮想ネットワーク（通常はvirbr0など）からIPアドレスが自動割り当てされます。この割り当てられたIPを特定し、Ansibleを実行する具体的な手順は以下の通りです。

#### VMの起動とIPアドレスの特定

まず、VMを起動してLibvirtが割り当てたIPアドレスを特定します。Libvirtのネットワーク管理コマンド（virsh）を使用します。

* 
* LibvirtのDHCPリース情報を確認するコマンド:

virsh net-dhcp-leases default

※ default はLibvirtのネットワーク名です。環境に合わせて変更してください。出力結果から該当するVMのMACアドレス、またはホスト名に対応するIPアドレスを控えます。

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

#### RHEL 5特有の注意点（重要）

RHEL 5は非常に古いOS（Python 2.4が標準）であるため、最新のAnsibleはそのままでは動作しません。以下の2点の事前準備、または対策が必要です。

* 
* Python 2.6以上の導入:
Ansibleを対象サーバーで動かすには、最低でもPython 2.6（Ansibleの古いバージョンを使用する場合）またはPython 2.7以降が必要です。プロビジョニング前に、VM側でEPELリポジトリなどからpython26などのパッケージを導入しておくか、手動でPythonをインストールしておく必要があります。
* Ansibleバージョンの選定:
最新のAnsible（2.10以降やAnsible Core）はPython 2.6/2.7のサポートを終了しています。RHEL 5を制御する場合、ローカル（コントロールノード）側で古いバージョンのAnsible（例: Ansible 2.4〜2.9など）を使用するか、raw モジュール（Python不問でSSHコマンドを直接実行するモジュール）を駆使する必要があります。
* 

#### Ansibleインベントリの構築

特定したIPアドレスをAnsibleのインベントリファイル（hosts）に定義します。

[rhel5_vms]
192.168.122.50 ansible_user=root ansible_ssh_pass=YourPassword

※ SSH鍵認証が設定されている場合は、ansible_ssh_private_key_file を指定してください。

#### プロビジョニングの実行

Pythonのバージョン問題があるため、最初のステップとして raw モジュールを使い、静的IPアドレスへの変更や、必要なPython環境のセットアップを行うのが安全です。

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
