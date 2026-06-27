https://access.redhat.com/solutions/1242883

https://archives.fedoraproject.org/pub/archive/epel/5/i386/cloud-init-0.6.3-0.12.bzr532.el5.noarch.rpm

## Archived RPM dependency resolution

`cloud-init-0.6.3-0.12.bzr532.el5.noarch.rpm` is in the Fedora/EPEL archive.
Resolve it against archived yum metadata instead of checking RPMs one by one.

Example:

```sh
python3 infra/cloud-init/resolve_rpm_deps.py \
  cloud-init-0.6.3-0.12.bzr532.el5.noarch.rpm \
  --repo https://archives.fedoraproject.org/pub/archive/epel/5/i386/ \
  --repo http://vault.centos.org/5.11/os/i386/ \
  --repo http://vault.centos.org/5.11/updates/i386/
```

To copy the resolved RPM set into a local directory:

```sh
python3 infra/cloud-init/resolve_rpm_deps.py \
  cloud-init-0.6.3-0.12.bzr532.el5.noarch.rpm \
  --repo https://archives.fedoraproject.org/pub/archive/epel/5/i386/ \
  --repo http://vault.centos.org/5.11/os/i386/ \
  --repo http://vault.centos.org/5.11/updates/i386/ \
  --download-dir infra/cloud-init/rpms
```

The script caches `repodata` and downloaded RPMs under `.cache/rpm-deps`, so
repeat runs only read local files unless the cache is missing.

If the target RPM is not listed in the repo metadata, pass the URL directly and
add `--target-url`:

```sh
python3 infra/cloud-init/resolve_rpm_deps.py \
  https://archives.fedoraproject.org/pub/archive/epel/5/i386/cloud-init-0.6.3-0.12.bzr532.el5.noarch.rpm \
  --target-url \
  --repo https://archives.fedoraproject.org/pub/archive/epel/5/i386/ \
  --repo http://vault.centos.org/5.11/os/i386/ \
  --repo http://vault.centos.org/5.11/updates/i386/
```
