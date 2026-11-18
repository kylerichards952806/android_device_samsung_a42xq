## 18 Nov 2026 — 3.5 mm jack, UDFPS HBM, About phone and GPS

### Builds

* GAPPS `18.11.2026` built at 12:45 (2,505,495,553 bytes, md5 `a7f6fd45ee26cf1846fbea48193d9f86`); zero failures.
* VANILLA `18.11.2026` restarted at 13:14 after the release post review.

### Fixes

* kernel: `zt_ts_fod_event_report()` now calls `sysfs_notify()` on `/sys/class/sec/tsp/scrub_pos` (`93d9c4a`), so the `org.lineageos.sensor.udfps` subhal poll is woken on FOD events. The notification alone does not fix screen-off/AOD unlock: on hardware testing the sensor still does not initialise or light up while the panel is off, though screen-on UDFPS is unaffected. Open for the next build.
* kernel: `ss_panel_on_post()` clears `finger_mask_hbm_on` and cancels the HBM watchdog (`93d9c4a`). An unlock finishes in panel on, so the UDFPS mask-off event never arrives; the mask stayed set and `ss_brightness_dcs()` ignored every normal brightness update, which is why the slider did nothing and the panel stayed at full brightness after unlocking.
* common: allow `hal_audio_default` to read `sysfs_audio_writable` (`de1afba`). The earjack `state` node was labelled in `genfs_contexts` but never granted to any domain, so the Samsung audio HAL got `EACCES` reading `/sys/class/audio/earjack/state` and never saw the 3.5 mm jack being plugged in.
* a42xq: move the space-separated hardware strings into `product.prop` (`dc8bf90`). `PRODUCT_PRODUCT_PROPERTIES` splits its entries on whitespace, so About phone showed `48MP` and the device name `Galaxy`; the full `48MP + 8MP + 5MP + 5MP`, `Snapdragon 750G`, `720 x 1600, 60 Hz`, `5000 mAh` and `Galaxy A42 5G` values now land in `/product/etc/build.prop` through `TARGET_PRODUCT_PROP`.
* a42xq: default `assisted_gps_enabled` to `true` in a SettingsProvider overlay. AOSP ships the default as `false`; on a GMS install the Google Location Accuracy toggle is what writes `1`, and where that toggle never runs `GnssLocationProvider` keeps A-GPS off entirely - `getSuplMode()` returns `GNSS_POSITION_MODE_STANDALONE` and `toggleXtraDaemon()` writes `persist.sys.xtra-daemon.enabled=false` (`fdb80ca`). That property is a legacy QTI hook nothing here reads - no blob in the vendor tree references it, and `xtra-daemon` is forked by `loc_launcher` from `izat.conf` (`PROCESS_STATE=ENABLED`, empty `PROCESS_ARGUMENT`) either way - so the real effect of the setting on this stack is the SUPL mode.
* a42xq: add `config_gnssParameters` with `SUPL_HOST=supl.google.com` and `SUPL_PORT=7275`. The shipped `/vendor/etc/gps.conf` has `SUPL_HOST` commented out and `AGPS_CONFIG_INJECT = 0`, so `GnssConfiguration.getSuplHost()` returned `null`, `setSuplHostPort()` skipped `setAgpsServer()` and no build ever had a SUPL server (`fdb80ca`).

### Diagnostics

* Verified on the device: after enabling A-GPS the GNSS engine fixed in under 50 s with 15 satellites, 7.6 m horizontal accuracy (3.5 m fused), and Maps received 255 locations over about five minutes. Before the change the same request ran for 55 s with no fix at all while the phone sat at the same spot.
* The remaining Samsung GNSS log lines are benign on this port: `secGpsCb hasn't been set yet` (no Samsung framework client registers the secgps callback), `setGpsBatteryFlag() : file open error` (no `battery/gps` sysfs node on this kernel), `loc_read_sec_gps_conf: no secgps conf file` (Samsung never shipped one for this model) and the `RF_LOSS_*` warning (`gps.conf` ships every `RF_LOSS_*` key as 0). None of them block a fix.
* `xtra-daemon` needs no init service: `loc_launcher` (`init.qcom.rc`) reads `/vendor/etc/izat.conf` and forks `xtra-daemon` with no arguments as `gps` in `u:r:vendor_location:s0`, and it is running on this build. All its prerequisites are present (`izat.conf`, `xtra_root_cert.pem`, `/data/vendor/location`), and the empty supplementary group list is harmless because the kernel is built without `CONFIG_ANDROID_PARANOID_NETWORK`.

### Log sweep

* No app crashes, ANRs or `system_server` restarts on the current boot: `logcat -b crash` is empty, the events buffer has no `am_crash`/`am_anr`/`am_low_memory`, and dropbox has no entries.
* common: the `dex2oat` -> `privapp_data_file` denial cannot be fixed in policy. `system/sepolicy/private/domain.te` neverallows every `dir` permission on `privapp_data_file`, so the allow added in `5dc1d38` failed `sepolicy_neverallows` and aborted the build at the policydb step; it is reverted in `d014cd2`, with the file kept comment-only so the policy glob does not change. dexopt falls back to a profile-less compile and the AVC is log-only.
* Reviewed and left alone as benign: `WifiHAL: nl_recvmsgs failed: -5` plus `WifiStaIfaceAidlImpl: getLinkLayerStats failed (code 7)` (the WLAN driver does not export `LL_STATS_IFACE_INFO_TS_DUTY_CYCLE`; statistics only), `RILC: secOemNoti ... mSehBridgeIndication == NULL` / `QC-DS-LIB: No Registered Clients` (Samsung's SEH bridge has no AOSP client), the Samsung GNSS lines (`secGpsCb`, `secgps.conf`, `battery/gps`) and `system_server: No package ID 7f found` (GMS resources referenced from a framework config).

### Performance

* common: zram-only swap tuning in `init.qcom.post_boot.sh` (`de1afba`): `vm.swappiness=100`, `vm.page-cluster=0`, `vm.vfs_cache_pressure=60`. zram is the only swap device on this platform, so reclaim should target it and fault-around should read one 4 KB page instead of a 128 KB cluster.

### Known issues

* The 17 Nov zips predate all of the above; they need the next build.
* The a42xq vendor blob repository is still private, so a complete build needs access to it in addition to the four public trees.

## 17 Nov 2026 — SetupWizard re-enabled

### Fixes

* a42xq: Google SetupWizard is **enabled in optional mode** (`ro.setupwizard.mode=OPTIONAL`, `e51ba12`). The page lock/unlock loop and the airplane-mode-after-an-offline-first-boot behaviour that forced `DISABLED` in the 16 Nov build no longer reproduce, so first boot runs the wizard again while users can still skip it.
* 17 Nov zips already built: `ro.setupwizard.mode` was flipped inside `system/build.prop` with a same-length `DISABLED` -> `OPTIONAL` swap, the AVB hashtree footer regenerated, the block payload rebuilt against the existing transfer list and the package re-signed with the release key, so no full rebuild was needed to fix the shipped zips.

### Notes

* A device already running the 17 Nov build gets the same result without flashing: KernelSU-Next root plus `resetprop ro.setupwizard.mode OPTIONAL`, or a `post-fs-data.d` script for it to survive reboots. `setprop` itself is rejected because `ro.*` properties are read-only once init has set them, and `/system` is verity-enforcing, so a remount edit is not possible.

## 17 Nov 2026 — GAPPS prebuilt packaging fix

### Fixes

* a42xq: register the device tree's Soong namespace (`PRODUCT_SOONG_NAMESPACES += device/samsung/a42xq`) and give the GMS prebuilts unique module names (`A42xqExtServices`, `A42xqGmsCore`). `PRODUCT_PACKAGES += GoogleExtServices` was resolving to the empty dummy app in `vendor/pixel/gms/dummy-apps`, whose committed `AndroidManifest.xml` is 0 bytes, so `manifest_fixer` aborted the GAPPS build with `error: no element found: line 1, column 0`.
* a42xq: drop the `allow hal_nfc_default default_prop:file` rule from `3d16f7e`. Direct property-area access violates the `property.te` neverallows, so `sepolicy_neverallows` aborted the build in `checkpolicy` (`4 neverallow failures occurred`). The NFC HAL denial it silenced is log-only noise and the interface works without it.
* a42xq: mark both GMS prebuilts `preprocessed: true`. Soong rejects presigned prebuilt APKs that target SDK 30+ unless they are preprocessed, because its own signing would break the v2 signature. Both APKs already pass the zipalign and uncompressed JNI/dex checks that go with the flag.

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

* a42xq: Google SetupWizard is **temporarily disabled** (`ro.setupwizard.mode=DISABLED`) while its page lock/unlock bug is fixed. On this port it only advanced after locking and unlocking the screen on every page, and after an offline first boot it left airplane mode enabled. Framework provisioning defaults are used instead, so first boot lands on the launcher.
* a42xq: **Dolby Atmos is removed from this and all future builds.** The A42 5G blob set contains no Dolby DAP effect library under `/vendor/lib*/soundfx` and no `/vendor/etc` Dolby configuration, so the app only exposed a switch that did nothing and had no profiles to select. `AudioFX` stays enabled and is the working equalizer.
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
* sm7225-common: the enforcing bring-up itself is device policy, not an upstream patch: 71 `.te` files, 368 `allow` rules, 39 `dontaudit` rules, 108 `file_contexts` and 104 `genfs_contexts` entries. Every Samsung blob (radio, UDFPS, tee/keymaster/gatekeeper, NFC, camera, audio, display/composer, sensors, power, thermal, WiFi, Bluetooth, DRM, health, vold, init, macloader) has its own domain and labels; there are no `permissive` domains and no catch-all allows. The rules were added deny by deny from enforcing boots and re-checked after every blob update.

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
