## 17 Nov 2026 — log sweep

### Fixes

* kernel: enable `CONFIG_F2FS_FS_VERITY` and `CONFIG_EXT4_FS_VERITY`. `/data` is f2fs, but only the generic `CONFIG_FS_VERITY` was on, so every fs-verity ioctl returned `ENOTSUP`. Android 17 retries on every atomic settings write and logged `ResilientAtomicFile: Failed to verity-protect ... Operation not supported on transport endpoint` 1082 times plus 240 `AccessPersistence` failures in a single boot. Needs the next kernel build.

### Diagnostics

* SELinux: 49 denials since boot, none from `system_server` or app processes. Repeats are kernel `qipcrtr_socket` creates from kworkers, `rild` on `vendor_diag_device`, `nfc@1.2-service` reading `default_prop`, and Proton Pass reading `/proc/version`. All are vendor/platform policy gaps, not functional failures.
* `RILD`/`RILD2` `nlmsg_type = 16` and `WifiHAL` QCA `LL_STATS` attribute errors are vendor noise; telephony and WiFi work.
* `keystore2` GC logs `UNIMPLEMENTED` when invalidating blobs. Expected with Infinity-X's spoofing/keybox stack; key operations and **STRONG** Play Integrity are unaffected.
* Memory: 2 GB zram active with ~450 MB used; the OOM reaper kills background apps (Facebook, Gearhead) under 4 GB pressure. Expected, not a leak.
* `msm_vidc: Failed to create debugfs` and `pet_watchdog` lines are harmless vendor kernel noise.

## 17 Nov 2026 — first-boot and Dolby cleanup

### Fixes

* a42xq: skip Google SetupWizard (`ro.setupwizard.mode=DISABLED`). On this port it only advanced after locking and unlocking the screen on every page, and after an offline first boot it left airplane mode enabled. Framework provisioning defaults are used instead, so first boot lands on the launcher.
* a42xq: stop installing `SamsungDAP` (Dolby Atmos). The A42 5G blob set contains no Dolby DAP effect library under `/vendor/lib*/soundfx` and no `/vendor/etc` Dolby configuration, so the app only exposed a switch that did nothing and had no profiles to select. `AudioFX` stays enabled and is the working equalizer.
* a42xq: stop installing `com.google.android.extservices.apex`. The APEX is byte-identical to the prebuilt and its avbpubkey in `/system/etc/security/apex` matches the key embedded in the file, yet apexd marks it `isActive="false"` (same for `com.google.android.gmssystem` in `/product/apex`). Until that is root-caused the priv-app APK fallbacks are the supported path, and shipping the inactive APEXes would risk a duplicate package if apexd ever activates them.

### Known issues

* GAPPS payload audit: `Photos`, `CalendarGooglePrebuilt`, `PrebuiltGmail` and `Maps` exist in `vendor/pixel/gms` but are not in the product image. Gmail, Maps and Play services arrive through Play Store updates instead; Photos and Calendar are not installed at all.

## 16 Nov 2026 — Drop the GMS APEX

### Build

* a42xq: stop installing `com.google.android.gmssystem.prodvic.apex`. Play services now ships as the `PrebuiltGmsCore` priv-app fallback, and if apexd ever activates the APEX as well the build would contain two packages named `com.google.android.gms`. `device.mk` filters the module out of `PRODUCT_PACKAGES` and `PRODUCT_COPY_FILES`, and the vendor list no longer carries the APEX entry.

## 16 Nov 2026 — Play services fallback

### Fixes

* a42xq: ship Google Play services (`com.google.android.gms`) as a privileged app. GAPPS builds carry the GMS APEX (`com.google.android.gmssystem.prodvic.apex`) in the payload, but apexd never activates the Google APEXes on this device, so `com.google.android.gms` was never installed and Play Store died with `SecurityException: Failed to find provider com.google.android.gsf.gservices`. The APK extracted from that APEX (26.11.36) now installs to `/system/priv-app/PrebuiltGmsCore` together with its privapp allowlist and preinstalled-packages sysconfig. GitHub rejects files over 100 MB and blocks LFS on public forks, so the 217 MB APK is committed in <100 MB parts and device.mk assembles it at build time.

## 16 Nov 2026 — GAPPS boot loop fix

### Fixes

* a42xq: ship Google ExtServices (`com.google.android.ext.services`) as a privileged app. GAPPS builds carry the prebuilt `com.google.android.extservices` APEX in `/system/apex`, but apexd never activates it on this device, so `PackageManagerService` threw `Required services extension package is missing` while starting bootstrap services, `system_server` died every ~5 seconds and the device looped on the boot animation forever. The APK (extracted from the APEX) and its `privapp_allowlist` are now installed to `/system/priv-app/GoogleExtServices`, and both Google APEX public keys are copied to `/system/etc/security/apex/` so apexd can verify them if it ever can.

# Infinity-X 4.2 — Samsung Galaxy A42 5G (a42xq)

## Infinity-X 4.2 — 16 November 2026

### Boot

* sm7225-common: dropped the `vendor.lineage.livedisplay` AIDL HAL declaration from the device manifest. No daemon in the tree registers those AIDL interfaces, so `LineageHardwareManager.isSupportedAIDL()` blocked in `ServiceManager.waitForDeclaredService()` on the `android.display` thread. `ActivityManagerService.finishBooting()` therefore never returned, user 0 stayed in `BOOTING` (the device sat on "Phone is starting" with no launcher), and the Watchdog killed `system_server` every ~66 seconds.
* a42xq: added `Launcher3QuickStep` to the product. Nothing in the Infinity-X product pulled in a HOME activity, so even a device that finished booting had no launcher.

### Features

* a42xq: added Dolby Atmos — `hardware/samsung/packages/Dap` builds `org.lineageos.dap`, which registers a `com.android.settings.action.IA_SETTINGS` activity and appears under Settings → Sound. The app drives the vendor DAP audio effect (UUID `46d279d9-9be7-453d-9d7c-ef937f675587`); that effect library is not in the blob set, so the switch has no audible effect yet.
* a42xq: enabled AudioFX via `TARGET_INCLUDES_AUDIOFX := true` (the Infinity common config gates it behind that board flag).

### SELinux

* `system/sepolicy`: `crash_dump` may now ptrace `vold` on user builds. Both the rule and the `-vold` exemption in the neverallow were `userdebug_or_eng` only, so `user` builds could not capture vold stacks.
* `system/sepolicy`: `system_server` may read `binderfs_logs_transactions` on user builds, restoring binder transaction dumps for ANR and watchdog reports.
* `system/sepolicy`: added a `dontaudit` for SystemUI reading `ro.usb.uvc.enabled`. The `appdomain` neverallow keeps that read denied by design, so only the recurring audit denial is silenced.

### Build

* OTA packaging now runs with `ZIPOPT=-y`. Without it `zip` follows the absolute symlinks in the target-files `ROOT/` (`ROOT/d` → `/sys/kernel/debug`), walks the host sysfs and hangs the build for 20+ minutes.

# LineageOS 24.0 — Samsung Galaxy A42 5G (a42xq)

## Highlights

* First build of LineageOS 24.0 for a42xq with SELinux fully enforcing and the ROM signed with private keys.
* The lockscreen PIN now survives a reboot, and the platform picked up fixes for brightness, power hints, thermal reporting, charging and memory compression.

## Device trees

* a42xq: added the `libshim_samsungaudioparams` shim, fixing in-call audio on the sm7225 platform.
* a42xq: added the nested `vendor/samsung/sm7225-common/a42xq` Soong namespace so the device blobs resolve from the combined vendor repository.
* a42xq: under-display fingerprint geometry (sensor position and radius) is declared to the framework, so the prompt uses the UDFPS UI rather than the generic fallback.
* a42xq: no device-specific changes in this build. The lockscreen PIN, brightness, thermal, power hint and memory compression fixes all come from the shared sm7225 platform tree.

## ROM

* healthd: charging current is now reported in microamps (with a `bms/current_now` fallback), so the always-on display shows the real charging wattage instead of 0.0 W.
* lineage-sdk: LiveDisplay no longer blocks `system_server` at boot, which previously caused a black screen after wiping data.
* SystemUI: the fingerprint prompt message is no longer hidden behind the navigation bar.

## Kernel

* No kernel changes in this release.
