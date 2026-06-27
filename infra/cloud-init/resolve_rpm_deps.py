#!/usr/bin/env python3
"""Resolve RPM dependencies from archived yum repository metadata.

This intentionally uses only Python's standard library so it can run on hosts
without rpm/yum/dnf installed. It is aimed at archived EL5/EPEL packages where
dependency resolution is mostly a matter of reading static repodata.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import posixpath
import re
import shutil
import struct
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


COMMON_IGNORES = {
    "/bin/sh",
}

PRIMARY_NS = {
    "repo": "http://linux.duke.edu/metadata/repo",
    "common": "http://linux.duke.edu/metadata/common",
    "rpm": "http://linux.duke.edu/metadata/rpm",
    "filelists": "http://linux.duke.edu/metadata/filelists",
}

RPM_HEADER_MAGIC = b"\x8e\xad\xe8\x01"
RPM_TAG_NAME = 1000
RPM_TAG_VERSION = 1001
RPM_TAG_RELEASE = 1002
RPM_TAG_ARCH = 1022
RPM_TAG_REQUIRE_FLAGS = 1048
RPM_TAG_REQUIRE_NAME = 1049
RPM_TAG_REQUIRE_VERSION = 1050


@dataclass(frozen=True)
class Dep:
    name: str
    flags: str = ""
    epoch: str = "0"
    version: str = ""
    release: str = ""


@dataclass(frozen=True)
class Package:
    name: str
    arch: str
    epoch: str
    version: str
    release: str
    location: str
    repo_base: str
    provides: tuple[Dep, ...]
    requires: tuple[Dep, ...]

    @property
    def nevra(self) -> str:
        return f"{self.name}-{self.version}-{self.release}.{self.arch}"

    @property
    def url(self) -> str:
        return urllib.parse.urljoin(ensure_slash(self.repo_base), self.location)


def ensure_slash(value: str) -> str:
    return value if value.endswith("/") else value + "/"


def cache_path(cache_dir: Path, url: str, suffix: str = "") -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    parsed_name = posixpath.basename(urllib.parse.urlparse(url).path)
    return cache_dir / f"{digest}-{parsed_name}{suffix}"


def fetch(url: str, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_path(cache_dir, url)
    if out.exists() and out.stat().st_size > 0:
        return out
    with urllib.request.urlopen(url) as src, out.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    return out


def load_metadata_url(repo_base: str, cache_dir: Path, metadata_type: str) -> str:
    repomd_url = urllib.parse.urljoin(ensure_slash(repo_base), "repodata/repomd.xml")
    repomd = fetch(repomd_url, cache_dir)
    root = ET.parse(repomd).getroot()
    for item in root.findall("repo:data", PRIMARY_NS):
        if item.attrib.get("type") != metadata_type:
            continue
        location = item.find("repo:location", PRIMARY_NS)
        if location is None:
            continue
        href = location.attrib["href"]
        return urllib.parse.urljoin(ensure_slash(repo_base), href)
    raise RuntimeError(f"{metadata_type} metadata not found in {repomd_url}")


def load_primary_url(repo_base: str, cache_dir: Path) -> str:
    return load_metadata_url(repo_base, cache_dir, "primary")


def load_filelists_url(repo_base: str, cache_dir: Path) -> str:
    return load_metadata_url(repo_base, cache_dir, "filelists")


def parse_dep(element: ET.Element) -> Dep:
    return Dep(
        name=element.attrib["name"],
        flags=element.attrib.get("flags", ""),
        epoch=element.attrib.get("epoch", "0") or "0",
        version=element.attrib.get("ver", ""),
        release=element.attrib.get("rel", ""),
    )


def parse_primary(repo_base: str, cache_dir: Path) -> list[Package]:
    primary_url = load_primary_url(repo_base, cache_dir)
    primary = fetch(primary_url, cache_dir)
    opener = gzip.open if primary.name.endswith(".gz") else open
    packages: list[Package] = []
    with opener(primary, "rb") as fh:
        for _, elem in ET.iterparse(fh, events=("end",)):
            if elem.tag != f"{{{PRIMARY_NS['common']}}}package":
                continue
            name = elem.findtext("common:name", namespaces=PRIMARY_NS) or ""
            arch = elem.findtext("common:arch", namespaces=PRIMARY_NS) or ""
            version = elem.find("common:version", PRIMARY_NS)
            location = elem.find("common:location", PRIMARY_NS)
            fmt = elem.find("common:format", PRIMARY_NS)
            if version is None or location is None or fmt is None:
                elem.clear()
                continue
            provides_parent = fmt.find("rpm:provides", PRIMARY_NS)
            requires_parent = fmt.find("rpm:requires", PRIMARY_NS)
            provides = tuple(
                parse_dep(e) for e in provides_parent.findall("rpm:entry", PRIMARY_NS)
            ) if provides_parent is not None else ()
            requires = tuple(
                parse_dep(e) for e in requires_parent.findall("rpm:entry", PRIMARY_NS)
            ) if requires_parent is not None else ()
            packages.append(
                Package(
                    name=name,
                    arch=arch,
                    epoch=version.attrib.get("epoch", "0") or "0",
                    version=version.attrib.get("ver", ""),
                    release=version.attrib.get("rel", ""),
                    location=location.attrib["href"],
                    repo_base=repo_base,
                    provides=provides,
                    requires=requires,
                )
            )
            elem.clear()
    return packages


def split_version(value: str) -> tuple[tuple[int, object], ...]:
    parts: list[tuple[int, object]] = []
    for token in re.findall(r"[0-9]+|[A-Za-z]+", value):
        if token.isdigit():
            parts.append((1, int(token)))
        else:
            parts.append((0, token))
    return tuple(parts)


def sort_key(pkg: Package) -> tuple[object, ...]:
    epoch = int(pkg.epoch or 0)
    return (pkg.name, epoch, split_version(pkg.version), split_version(pkg.release))


def dep_key(dep: Dep) -> str:
    return dep.name


def is_builtin(dep: Dep) -> bool:
    return (
        dep.name in COMMON_IGNORES
        or dep.name.startswith("rpmlib(")
        or dep.name.startswith("config(")
    )


def build_provider_index(packages: Iterable[Package]) -> dict[str, list[Package]]:
    index: dict[str, list[Package]] = {}
    for pkg in packages:
        index.setdefault(pkg.name, []).append(pkg)
        for provide in pkg.provides:
            index.setdefault(provide.name, []).append(pkg)
    for candidates in index.values():
        candidates.sort(key=sort_key, reverse=True)
    return index


def package_identity(pkg: Package) -> tuple[str, str, str, str, str]:
    return (pkg.name, pkg.arch, pkg.epoch or "0", pkg.version, pkg.release)


def add_file_providers(
    packages: Iterable[Package],
    providers: dict[str, list[Package]],
    repo_bases: Iterable[str],
    cache_dir: Path,
    needed_files: set[str],
) -> None:
    by_identity = {package_identity(pkg): pkg for pkg in packages}
    by_nevra = {
        (pkg.name, pkg.arch, pkg.version, pkg.release): pkg
        for pkg in packages
    }
    unresolved = set(needed_files)
    for repo_base in repo_bases:
        if not unresolved:
            break
        filelists_url = load_filelists_url(repo_base, cache_dir)
        filelists = fetch(filelists_url, cache_dir)
        opener = gzip.open if filelists.name.endswith(".gz") else open
        with opener(filelists, "rb") as fh:
            for _, elem in ET.iterparse(fh, events=("end",)):
                if elem.tag != f"{{{PRIMARY_NS['filelists']}}}package":
                    continue
                name = elem.attrib.get("name", "")
                arch = elem.attrib.get("arch", "")
                version = elem.find("filelists:version", PRIMARY_NS)
                if version is None:
                    elem.clear()
                    continue
                identity = (
                    name,
                    arch,
                    version.attrib.get("epoch", "0") or "0",
                    version.attrib.get("ver", ""),
                    version.attrib.get("rel", ""),
                )
                pkg = by_identity.get(identity)
                if pkg is None:
                    pkg = by_nevra.get((identity[0], identity[1], identity[3], identity[4]))
                if pkg is not None:
                    for file_elem in elem.findall("filelists:file", PRIMARY_NS):
                        filename = file_elem.text or ""
                        if filename in unresolved:
                            providers.setdefault(filename, []).append(pkg)
                            unresolved.remove(filename)
                elem.clear()
    for filename in needed_files:
        providers.setdefault(filename, []).sort(key=sort_key, reverse=True)


def find_target(target: str, packages: list[Package]) -> Package | None:
    target_base = posixpath.basename(urllib.parse.urlparse(target).path)
    for pkg in packages:
        if posixpath.basename(pkg.location) == target_base:
            return pkg
    by_name = [pkg for pkg in packages if pkg.name == target]
    if by_name:
        return sorted(by_name, key=sort_key, reverse=True)[0]
    return None


def resolve(targets: list[Package], providers: dict[str, list[Package]]) -> tuple[list[Package], list[Dep]]:
    chosen: dict[str, Package] = {}
    missing: dict[str, Dep] = {}
    queue = list(targets)
    while queue:
        pkg = queue.pop(0)
        if pkg.name in chosen:
            continue
        chosen[pkg.name] = pkg
        for dep in pkg.requires:
            if is_builtin(dep):
                continue
            provider = providers.get(dep_key(dep), [None])[0]
            if provider is None:
                missing[dep.name] = dep
                continue
            if provider.name not in chosen:
                queue.append(provider)
    return sorted(chosen.values(), key=lambda p: p.name), sorted(missing.values(), key=lambda d: d.name)


def resolve_with_filelists(
    targets: list[Package],
    packages: list[Package],
    providers: dict[str, list[Package]],
    repo_bases: Iterable[str],
    cache_dir: Path,
) -> tuple[list[Package], list[Dep]]:
    seen_files: set[str] = set()
    while True:
        resolved, missing = resolve(targets, providers)
        missing_files = {dep.name for dep in missing if dep.name.startswith("/")}
        new_files = missing_files - seen_files
        if not new_files:
            return resolved, missing
        seen_files.update(new_files)
        add_file_providers(packages, providers, repo_bases, cache_dir, new_files)


def read_cstring_store(data: bytes, start: int, count: int) -> list[str]:
    values = []
    pos = start
    for _ in range(count):
        end = data.index(0, pos)
        values.append(data[pos:end].decode("utf-8", "replace"))
        pos = end + 1
    return values


def read_header(data: bytes, pos: int) -> tuple[list[tuple[int, int, int, int]], int, int]:
    if data[pos:pos + 4] != RPM_HEADER_MAGIC:
        raise RuntimeError(f"RPM header magic not found at offset {pos}")
    pos += 8
    index_count, store_size = struct.unpack(">II", data[pos:pos + 8])
    pos += 8
    entries = []
    for _ in range(index_count):
        entries.append(struct.unpack(">IIII", data[pos:pos + 16]))
        pos += 16
    store_start = pos
    return entries, store_start, store_start + store_size


def rpm_tag(data: bytes, entries: list[tuple[int, int, int, int]], store_start: int, tag: int):
    found = next((entry for entry in entries if entry[0] == tag), None)
    if found is None:
        return None
    _, typ, offset, count = found
    start = store_start + offset
    if typ in (8, 9):
        return read_cstring_store(data, start, count)
    if typ == 6:
        return read_cstring_store(data, start, 1)[0]
    if typ == 4:
        return list(struct.unpack(">" + "I" * count, data[start:start + 4 * count]))
    return None


def rpm_scalar(data: bytes, entries: list[tuple[int, int, int, int]], store_start: int, tag: int) -> str:
    value = rpm_tag(data, entries, store_start, tag)
    return value if isinstance(value, str) else ""


def rpm_entries(rpm_path: Path) -> tuple[list[tuple[int, int, int, int]], int, bytes]:
    data = rpm_path.read_bytes()
    pos = 96
    _, _, end = read_header(data, pos)
    pos = end
    while pos % 8:
        pos += 1
    entries, store_start, _ = read_header(data, pos)
    return entries, store_start, data


def rpm_requires(rpm_path: Path) -> list[Dep]:
    entries, store_start, data = rpm_entries(rpm_path)
    names = rpm_tag(data, entries, store_start, RPM_TAG_REQUIRE_NAME) or []
    versions = rpm_tag(data, entries, store_start, RPM_TAG_REQUIRE_VERSION) or [""] * len(names)
    flags = rpm_tag(data, entries, store_start, RPM_TAG_REQUIRE_FLAGS) or [0] * len(names)
    deps = []
    for name, version, flag in zip(names, versions, flags):
        op = ""
        if flag & 0x2 and flag & 0x8:
            op = "LE"
        elif flag & 0x4 and flag & 0x8:
            op = "GE"
        elif flag & 0x2:
            op = "LT"
        elif flag & 0x4:
            op = "GT"
        elif flag & 0x8:
            op = "EQ"
        deps.append(Dep(name=name, flags=op, version=version))
    return deps


def rpm_package_from_url(url: str, cache_dir: Path) -> Package:
    rpm_path = fetch(url, cache_dir)
    entries, store_start, data = rpm_entries(rpm_path)
    name = rpm_scalar(data, entries, store_start, RPM_TAG_NAME)
    version = rpm_scalar(data, entries, store_start, RPM_TAG_VERSION)
    release = rpm_scalar(data, entries, store_start, RPM_TAG_RELEASE)
    arch = rpm_scalar(data, entries, store_start, RPM_TAG_ARCH)
    parsed = urllib.parse.urlparse(url)
    repo_base = urllib.parse.urlunparse(parsed._replace(path=posixpath.dirname(parsed.path), params="", query="", fragment=""))
    location = posixpath.basename(parsed.path)
    return Package(
        name=name,
        arch=arch,
        epoch="0",
        version=version,
        release=release,
        location=location,
        repo_base=repo_base,
        provides=(Dep(name=name, flags="EQ", version=version, release=release),),
        requires=tuple(rpm_requires(rpm_path)),
    )


def download_packages(packages: Iterable[Package], output_dir: Path, cache_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for pkg in packages:
        src = fetch(pkg.url, cache_dir)
        dst = output_dir / posixpath.basename(pkg.location)
        if not dst.exists():
            shutil.copy2(src, dst)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="+", help="RPM URL, RPM basename, or package name")
    parser.add_argument(
        "--repo",
        action="append",
        required=True,
        help="Yum repo base URL containing repodata/. Use multiple times.",
    )
    parser.add_argument(
        "--cache-dir",
        default=".cache/rpm-deps",
        help="metadata/RPM cache directory",
    )
    parser.add_argument(
        "--download-dir",
        help="copy resolved RPMs to this directory",
    )
    parser.add_argument(
        "--target-url",
        action="store_true",
        help="download and inspect target URLs even if they are absent from repo metadata",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cache_dir = Path(args.cache_dir)
    packages: list[Package] = []
    for repo in args.repo:
        packages.extend(parse_primary(repo, cache_dir))

    providers = build_provider_index(packages)
    targets: list[Package] = []
    missing: list[Dep] = []
    for target in args.target:
        pkg = find_target(target, packages)
        if pkg is not None:
            targets.append(pkg)
            continue
        if args.target_url and target.startswith(("http://", "https://")):
            targets.append(rpm_package_from_url(target, cache_dir))
            continue
        print(f"target not found in repo metadata: {target}", file=sys.stderr)
        return 2

    resolved, unresolved = resolve_with_filelists(targets, packages, providers, args.repo, cache_dir)
    missing.extend(unresolved)

    print("# resolved")
    for pkg in resolved:
        print(pkg.url)
    if missing:
        print("\n# unresolved")
        for dep in missing:
            suffix = f" {dep.flags} {dep.version}".rstrip() if dep.flags or dep.version else ""
            print(f"{dep.name}{suffix}")

    if args.download_dir:
        download_packages(resolved, Path(args.download_dir), cache_dir)

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
