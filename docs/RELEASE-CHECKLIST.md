# Release checklist

- [ ] Verify all added community images/audio have redistribution permission.
- [ ] Build ISO on updated Arch Linux x86_64.
- [ ] Boot under UEFI and inspect GRUB.
- [ ] Boot under BIOS if BIOS support is part of the release target.
- [ ] Confirm SDDM autologin and temporary live-user setup.
- [ ] Confirm NetworkManager, audio, Firefox, Dolphin, Discover.
- [ ] Confirm wallpaper first-run and soundboard playback.
- [ ] Test install to disposable VM using Archinstall + GRUB.
- [ ] Verify installed system starts and updates.
- [ ] Add Calamares only after its package source, module set, partitioning behavior and GRUB install are validated.
- [ ] Sign the ISO checksum and publish release notes.
