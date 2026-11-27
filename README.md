# OnePlus 12 KernelSU + SUSFS

GKI AnyKernel3 builds for the OnePlus 12 (`waffle` / SM8650) with KernelSU Next and SUSFS, built from OnePlus official sources (`OnePlusOSS`) and the WildKernels patch stack.

Latest builds: [Releases](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS/releases)

## Disclaimer

Flashing a custom kernel can cause bootloops or data loss. Before flashing:

- Back up your data and your stock `boot.img` / `init_boot.img`.
- Know how to restore the stock boot images with `fastboot`.

You flash this kernel at your own risk.

## Device and compatibility

| Property | Value |
|---|---|
| Device | OnePlus 12 (`waffle`) |
| Models | `CPH2573`, `CPH2581`, `CPH2583` (`EX01`), `PJD110` (`CN01`) |
| SoC / platform | Snapdragon 8 Gen 3 (`SM8650` / `pineapple`) |
| Kernel KMI | `android14-6.1` |
| ROMs | Stock ColorOS 17 (current); older builds: stock OxygenOS / ColorOS 14–16 |
| Kernel `uname` | `<kernel>-android14-OP12-SUSFS` |

> **Note:** OnePlus has discontinued OxygenOS. From version 17 onward the stock firmware is **ColorOS 17**, and all builds here target ColorOS 17 going forward.

### Supported OS and kernel versions

| OS version | Kernel version(s) | Source tree |
|---|---|---|
| Android 17 | `android14-6.1.157` | [Enawba/android_kernel_common_oneplus_sm8650](https://github.com/Enawba/android_kernel_common_oneplus_sm8650/tree/oneplus/sm8650_c_17.0.0_oneplus12) (6.1.141 to 6.1.157, `android14-6.1-2025-12_r24` merge) |
| Android 16 | `android14-6.1.141`, `android14-6.1.118` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |
| Android 15 | `android14-6.1.118`, `android14-6.1.75` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |
| Android 14 | `android14-6.1.57` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |

Check that your running kernel (`uname -r`) matches the ZIP version before flashing. Do not flash a kernel with a lower sublevel than your installed firmware.

## Features

- KernelSU / KernelSU Next root, compatible with the WildKSU manager
- SUSFS (`susfs4ksu`): mount, path, kstat, uname, cmdline and memory-map hiding, plus ADB JDWP socket hiding
- Baseband Guard (BBG): LSM that protects critical partitions
- BBRv1 and BBRv3 TCP congestion control
- CAKE and PIE qdiscs
- ThinLTO
- MLGO (`-mllvm -regalloc-enable-advisor=release`), only when the toolchain Clang supports it. The stock OP12 Clang `r487747c` does not.
- Memory, I/O, CPU scheduler and network tuning patches
- TTL / HL target support
- IP set and IPv6 NAT
- tmpfs xattr and POSIX ACL (for meta-modules and Mountify)
- Unicode bypass fix for path traversal using non-printable codepoints
- Droidspaces container support
- NTSync
- Faster SDP charging: 900 mA instead of 500 mA on USB data ports that support it (USB 3.0)

## Installation

Requirements:

- Unlocked bootloader
- Backup of the stock `boot.img` / `init_boot.img` for your exact ColorOS build
- Existing root (Magisk, KernelSU or APatch) to use Kernel Flasher

Steps:

1. Download the `AK3_OP12_*.zip` that matches your Android and kernel version from [Releases](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS/releases).
2. If you are switching from another root method:
   - Magisk: do a full Magisk uninstall after flashing the ZIP.
   - KernelSU LKM (patched `init_boot` / `boot`): restore the stock image first so LKM does not conflict with GKI KernelSU.
   - APatch: clean up `/data/adb` leftovers after flashing the ZIP.
3. Flash the ZIP to the active slot with [Kernel Flasher](https://github.com/fatalcoder524/KernelFlasher/releases).
4. Install the [KernelSU Next](https://github.com/KernelSU-Next/KernelSU-Next/releases) or [WildKSU](https://github.com/WildKernels/Wild_KSU/releases) manager, then flash [ksu_module_susfs](https://github.com/sidex15/ksu_module_susfs/releases) from the manager.
5. Reboot and check `uname -r` and root status.

## Upstream source monitor

The [`op12-source-monitor.yml`](.github/workflows/op12-source-monitor.yml) workflow checks [`OnePlusOSS`](https://github.com/OnePlusOSS) every 12 hours, and on manual dispatch, for OnePlus 12 updates in:

- `OnePlusOSS/kernel_manifest` (`oneplus/sm8650` files matching `oneplus_12*`)
- `OnePlusOSS/android_kernel_common_oneplus_sm8650`, `android_kernel_modules_and_devicetree_oneplus_sm8650` and `android_kernel_oneplus_sm8650` (`*oneplus12*` / `waffle` branches, commit SHAs and `Makefile` sublevels)
- New `SM8650` / OnePlus 12 repositories

State is stored on the [`monitor-state`](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS/tree/monitor-state) branch. A new branch, manifest or kernel update opens an issue labeled `op12-source-update`.

## Links

- [WildKernels kernel patches](https://github.com/WildKernels/kernel_patches)
- [Kernel Flasher](https://github.com/fatalcoder524/KernelFlasher)
- [KernelSU Next manager](https://github.com/KernelSU-Next/KernelSU-Next/releases) / [WildKSU manager](https://github.com/WildKernels/Wild_KSU/releases)
- [SUSFS userspace module](https://github.com/sidex15/ksu_module_susfs/releases)

## Credits

Based on [WildKernels/OnePlus_KernelSU_SUSFS](https://github.com/WildKernels/OnePlus_KernelSU_SUSFS) by fatalcoder524 and contributors.

- [WildKernels kernel patches](https://github.com/WildKernels/kernel_patches)
- [KernelSU](https://github.com/tiann/KernelSU) by tiann
- [KernelSU Next](https://github.com/KernelSU-Next/KernelSU-Next) by rifsxd
- [Magic-KSU](https://github.com/5ec1cff/KernelSU) by 5ec1cff
- [SUSFS](https://gitlab.com/simonpunk/susfs4ksu) by simonpunk
- [SUSFS module](https://github.com/sidex15/ksu_module_susfs) by sidex15
- [AnyKernel3](https://github.com/osm0sis/AnyKernel3) by osm0sis
- [Baseband Guard](https://github.com/vc-teahouse/Baseband-guard) by vc-teahouse
- [Droidspaces](https://github.com/ravindu644/Droidspaces-OSS) by ravindu644
- [OnePlus kernel source](https://github.com/OnePlusOSS) by OnePlusOSS

## Issues

Report problems with these builds in [Enawba/OnePlus12_KernelSU_SUSFS issues](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS/issues).
