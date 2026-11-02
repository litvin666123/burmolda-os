#!/usr/bin/env python3
"""Customize a writable copy of Archiso's official releng profile."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import sys

PACKAGES = [
    "plasma-meta", "sddm", "sddm-kcm", "networkmanager", "pipewire",
    "pipewire-alsa", "pipewire-pulse", "wireplumber", "firefox", "dolphin", "konsole",
    "ark", "spectacle", "vlc", "pavucontrol", "plasma-nm", "plasma-pa",
    "bluedevil", "discover", "packagekit-qt6", "archinstall", "grub",
    "os-prober", "efibootmgr", "sudo", "git", "fastfetch", "htop",
    "base-devel", "xdg-user-dirs", "7zip", "unzip", "zip",
]


def copy_tree(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir() and not item.is_symlink():
            shutil.copytree(item, target, dirs_exist_ok=True, symlinks=True)
        elif item.is_symlink():
            if target.exists() or target.is_symlink():
                target.unlink()
            target.symlink_to(item.readlink())
        else:
            shutil.copy2(item, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--grub-dir", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--wallpapers", required=True, type=Path)
    parser.add_argument("--sounds", required=True, type=Path)
    args = parser.parse_args()

    profiledef = args.profile / "profiledef.sh"
    packages_file = args.profile / "packages.x86_64"
    if not profiledef.is_file() or not packages_file.is_file():
        print("Archiso releng profile is missing profiledef.sh or packages.x86_64.", file=sys.stderr)
        return 2

    text = profiledef.read_text(encoding="utf-8")
    label = "BURMOLDA_" + datetime.now(timezone.utc).strftime("%Y%m")
    replacements = {
        "iso_name": '"burmolda"',
        "iso_label": f'"{label}"',
        "iso_publisher": '"Burmolda OS Project"',
        "iso_application": '"Burmolda OS Live/Rescue Media"',
        "iso_version": f'"{args.version}"',
        "install_dir": '"burmolda"',
    }
    for key, value in replacements.items():
        pattern = rf"(?m)^{key}=.*$"
        if re.search(pattern, text):
            text = re.sub(pattern, f"{key}={value}", text, count=1)
        else:
            text += f"\\n{key}={value}\\n"

    # Archiso's current GRUB mode is named uefi.grub.
    text = text.replace("uefi.systemd-boot", "uefi.grub")
    if "uefi.grub" not in text:
        bootmodes = re.search(r"(?ms)^bootmodes=\\((.*?)\\)", text)
        if not bootmodes:
            print("Could not enable UEFI GRUB: unsupported profiledef.sh format.", file=sys.stderr)
            return 3
        block = re.sub(r"\\s*'uefi[^']*systemd-boot[^']*'", "", bootmodes.group(1)).rstrip()
        text = text[:bootmodes.start(1)] + block + " 'uefi.grub'" + text[bootmodes.end(1):]
    profiledef.write_text(text, encoding="utf-8")

    existing = packages_file.read_text(encoding="utf-8")
    with packages_file.open("a", encoding="utf-8") as out:
        out.write("\\n# Burmolda OS desktop and utilities\\n")
        for package in PACKAGES:
            if not re.search(rf"(?m)^\\s*{re.escape(package)}\\s*$", existing):
                out.write(package + "\\n")

    copy_tree(args.overlay, args.profile / "airootfs")

    # GitHub's contents API stores text files as 0644; restore live script permissions.
    live_bin = args.profile / "airootfs/usr/local/bin"
    for script in live_bin.iterdir():
        if script.is_file():
            script.chmod(0o755)
    sudoers_dir = args.profile / "airootfs/etc/sudoers.d"
    for sudoers in sudoers_dir.iterdir():
        if sudoers.is_file():
            sudoers.chmod(0o440)

    systemd_root = args.profile / "airootfs/etc/systemd/system"
    multi_user = systemd_root / "multi-user.target.wants"
    graphical = systemd_root / "graphical.target.wants"
    multi_user.mkdir(parents=True, exist_ok=True)
    graphical.mkdir(parents=True, exist_ok=True)
    links = {
        multi_user / "burmolda-live-setup.service": "../burmolda-live-setup.service",
        multi_user / "NetworkManager.service": "/usr/lib/systemd/system/NetworkManager.service",
        graphical / "sddm.service": "/usr/lib/systemd/system/sddm.service",
    }
    for path, target in links.items():
        if path.exists() or path.is_symlink():
            path.unlink()
        path.symlink_to(target)
    default_target = systemd_root / "default.target"
    if default_target.exists() or default_target.is_symlink():
        default_target.unlink()
    default_target.symlink_to("/usr/lib/systemd/system/graphical.target")

    copy_tree(args.grub_dir, args.profile / "grub")
    if not (args.profile / "grub/grub.cfg").is_file():
        print("Burmolda GRUB configuration is missing.", file=sys.stderr)
        return 4
    copy_tree(args.wallpapers, args.profile / "airootfs/usr/share/backgrounds/burmolda/community")
    copy_tree(args.sounds, args.profile / "airootfs/usr/share/burmolda/sounds/community")
    print(f"Prepared profile {args.profile}; UEFI=GRUB; BIOS=Syslinux; ISO label={label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
