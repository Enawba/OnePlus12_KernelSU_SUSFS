# Compatibility — OnePlus 12 (`waffle` / `SM8650`)

## Supported Device

- **Device:** OnePlus 12 (`waffle`)
- **Hardware Models:** `CPH2573`, `CPH2581`, `CPH2583`, `PJD110`
- **SoC:** Qualcomm Snapdragon 8 Gen 3 (`SM8650` / `pineapple`)
- **Kernel KMI:** `android14-6.1`
- **Supported ROMs:** Stock OxygenOS / ColorOS only

> **Important:**
> - Always back up your stock `boot.img` / `init_boot.img` before flashing.
> - Match the kernel sublevel in the ZIP filename to your installed firmware (`uname -r`). Never flash a lower kernel sublevel than your running OS.

## Kernel Version Matrix

| OS Version | Kernel Version(s) | Kernel Source Base |
|---|---|---|
| Android 17 | `android14-6.1.157` | `Enawba/android_kernel_common_oneplus_sm8650` (`oneplus/sm8650_c_17.0.0_oneplus12`) |
| Android 16 | `android14-6.1.141`, `android14-6.1.118` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |
| Android 15 | `android14-6.1.118`, `android14-6.1.75` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |
| Android 14 | `android14-6.1.57` | `OnePlusOSS/android_kernel_common_oneplus_sm8650` |
