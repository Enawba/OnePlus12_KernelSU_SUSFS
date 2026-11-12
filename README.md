<div align="center">

# OnePlus 12 KernelSU + SUSFS

[![Device](https://img.shields.io/badge/Device-OnePlus%2012%20(waffle%20%2F%20SM8650)-red)](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS)
[![KernelSU-Next](https://img.shields.io/badge/KernelSU_Next-Supported-green)](https://kernelsu-next.github.io/webpage/)
[![KernelSU](https://img.shields.io/badge/KernelSU-Supported-green)](https://kernelsu.org/)
[![SUSFS](https://img.shields.io/badge/SUSFS-Integrated-orange?logo=gitlab)](https://gitlab.com/simonpunk/susfs4ksu)
[![Releases](https://img.shields.io/github/v/release/Enawba/OnePlus12_KernelSU_SUSFS?label=Latest%20Release)](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS/releases)

</div>

---

## ⚠️ Disclaimer

Flashing a custom kernel carries a risk of bootloops or data loss. Please make sure to:
- 💾 Back up your data and your stock `boot.img` / `init_boot.img` before flashing
- 🧠 Understand how to restore stock boot images via `fastboot` if needed
- By flashing this kernel, **YOU** are choosing to make these modifications and assume full responsibility.

<div align="center">

# **🚨 Proceed at your own risk!**

</div>

---

## 📱 Device Information & Compatibility

This repository builds **OnePlus 12 (`waffle`)** GKI AnyKernel3 packages based on OnePlus Official Sources (`OnePlusOSS`) and WildKernels' patch stack.

| Property | Value |
|---|---|
| **Device** | OnePlus 12 (`waffle`) |
| **Supported Models** | `CPH2573`, `CPH2581`, `CPH2583` (`EX01`), `PJD110` (`CN01`) |
| **SoC / Platform** | Qualcomm Snapdragon 8 Gen 3 (`SM8650` / `pineapple`) |
| **Kernel KMI** | `android14-6.1` |
| **Supported ROMs** | Stock OxygenOS / ColorOS only |
| **Kernel `uname` Suffix** | `OP12-SUSFS` *(from next release onwards; `v2.4.0-r1` used `OP-WILD`)* |

### Supported OS & Kernel Versions

| OS Version | Kernel Version(s) | Source Tree |
|---|---|---|
| **Android 17** | `android14-6.1.157` | [Enawba/android_kernel_common_oneplus_sm8650](https://github.com/Enawba/android_kernel_common_oneplus_sm8650/tree/oneplus/sm8650_c_17.0.0_oneplus12) *(6.1.141 → 6.1.157 `android14-6.1-2025-12_r24` merge)* |
| **Android 16** | `android14-6.1.141`, `android14-6.1.118` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |
| **Android 15** | `android14-6.1.118`, `android14-6.1.75` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |
| **Android 14** | `android14-6.1.57` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |

> **Note:** Always verify your running kernel (`uname -r`) matches the target ZIP version before flashing. Do not flash an older kernel sublevel than your installed firmware.

---

## 🔗 Additional Resources

- 📦 [Releases (AnyKernel3 ZIPs)](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS/releases)
- 🩹 [WildKernels Kernel Patches](https://github.com/WildKernels/kernel_patches)
- ⚡ [Kernel Flasher](https://github.com/fatalcoder524/KernelFlasher)
- 🔧 [KernelSU-Next Manager](https://github.com/KernelSU-Next/KernelSU-Next/releases) / [WildKSU Manager](https://github.com/WildKernels/Wild_KSU/releases)
- 🥷 [SUSFS Userspace Module](https://github.com/sidex15/ksu_module_susfs/releases)

---

## ✨ Features

- 🔐 **KernelSU / KernelSU-Next**: Kernel-mode root solution for Android GKI devices
- 🔥 **WildKSU Manager Support**: Compatible with WildKernels' custom root manager
- 🥷 **SUSFS**: Integrated `susfs4ksu` kernel patches for mount, path, kstat, uname, cmdline, and memory-map hiding
- 🛡️ **BBG (Baseband Guard)**: LSM-based security protecting critical device partitions
- 🖧 **BBRv1 & BBRv3**: Improved TCP congestion control
- 🚦 **CAKE & PIE qdisc Support**: Better network schedulers
- ✅ **Thin LTO**: Link Time Optimization enabled
- 🚀 **Optimisation Patches**: Memory, I/O, CPU scheduler, and network tunings
- 🌐 **TTL Target Support**: Network packet TTL/HL modification
- 🧱 **IP Set & IPv6 NAT Support**: Advanced firewall and IPv6 NAT capabilities
- ⚡️ **TMPFS XATTR / POSIX ACL**: Extended tmpfs support for meta-modules and Mountify
- </> **Unicode Bypass Fix**: Mitigates path traversal detections using non-printable Unicode codepoints
- 🖥️ **Droidspaces Support**: Portable Linux container support
- 🔃 **NTSync**: Low-latency Windows NT synchronization primitives

---

## 📋 Installation Instructions

### Prerequisites
- Unlocked bootloader on your **OnePlus 12**
- Stock `boot.img` / `init_boot.img` backed up for your exact current OxygenOS/ColorOS build
- Existing root access (Magisk / KernelSU / APatch) to flash via Kernel Flasher

### Steps (via Kernel Flasher)
1. Download the matching `AK3_OP12_*.zip` for your Android & kernel version from [Releases](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS/releases).
2. If migrating from another root method:
   - **Magisk:** Perform a complete Magisk uninstall **after** flashing the AnyKernel3 ZIP.
   - **KernelSU LKM (`init_boot`/`boot` patched):** Restore stock `init_boot.img` / `boot.img` first so LKM does not conflict with GKI KernelSU.
   - **APatch:** Clean up `/data/adb` leftovers **after** flashing the AnyKernel3 ZIP.
3. Flash the AnyKernel3 ZIP to your active slot using [Kernel Flasher](https://github.com/fatalcoder524/KernelFlasher/releases).
4. Install the matching [KernelSU-Next](https://github.com/KernelSU-Next/KernelSU-Next/releases) (or [WildKSU](https://github.com/WildKernels/Wild_KSU/releases)) Manager APK and flash [sidex15/ksu_module_susfs](https://github.com/sidex15/ksu_module_susfs/releases) inside the manager.
5. Reboot and verify `uname -r` and root status.

---

## 🌟 Special Thanks

Based on **[WildKernels/OnePlus_KernelSU_SUSFS](https://github.com/WildKernels/OnePlus_KernelSU_SUSFS)** (`fatalcoder524` and contributors).

<div align="center">

| 🔧 **Project** | 👨‍💻 **Developer / Maintainer** | 🔗 **Link** |
|:---------------:|:----------------:|:-----------:|
| **WildKernels** | fatalcoder524 & contributors | [![GitHub](https://img.shields.io/badge/GitHub-WildKernels-blue?style=flat-square&logo=github)](https://github.com/WildKernels/OnePlus_KernelSU_SUSFS) |
| **Kernel Patches** | WildKernels | [![GitHub](https://img.shields.io/badge/GitHub-kernel__patches-blue?style=flat-square&logo=github)](https://github.com/WildKernels/kernel_patches) |
| **KernelSU** | tiann | [![GitHub](https://img.shields.io/badge/GitHub-tiann-blue?style=flat-square&logo=github)](https://github.com/tiann/KernelSU) |
| **KernelSU-Next** | rifsxd | [![GitHub](https://img.shields.io/badge/GitHub-rifsxd-blue?style=flat-square&logo=github)](https://github.com/KernelSU-Next/KernelSU-Next) |
| **Magic-KSU** | 5ec1cff | [![GitHub](https://img.shields.io/badge/GitHub-5ec1cff-blue?style=flat-square&logo=github)](https://github.com/5ec1cff/KernelSU) |
| **SUSFS** | simonpunk | [![GitLab](https://img.shields.io/badge/GitLab-simonpunk-orange?style=flat-square&logo=gitlab)](https://gitlab.com/simonpunk/susfs4ksu.git) |
| **SUSFS Module** | sidex15 | [![GitHub](https://img.shields.io/badge/GitHub-sidex15-blue?style=flat-square&logo=github)](https://github.com/sidex15/ksu_module_susfs) |
| **AnyKernel3** | osm0sis | [![GitHub](https://img.shields.io/badge/GitHub-osm0sis-blue?style=flat-square&logo=github)](https://github.com/osm0sis/AnyKernel3) |
| **Baseband Guard** | vc-teahouse | [![GitHub](https://img.shields.io/badge/GitHub-vc--teahouse-blue?style=flat-square&logo=github)](https://github.com/vc-teahouse/Baseband-guard.git) |
| **Droidspaces** | ravindu644 | [![GitHub](https://img.shields.io/badge/GitHub-ravindu644-blue?style=flat-square&logo=github)](https://github.com/ravindu644/Droidspaces-OSS.git) |
| **OnePlus Kernel Source** | OnePlusOSS | [![GitHub](https://img.shields.io/badge/GitHub-OnePlusOSS-blue?style=flat-square&logo=github)](https://github.com/OnePlusOSS) |

</div>

---

## 💬 Support

If you encounter any issues specific to these OnePlus 12 builds, open an issue in [Enawba/OnePlus12_KernelSU_SUSFS](https://github.com/Enawba/OnePlus12_KernelSU_SUSFS/issues).
