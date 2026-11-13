# LineageOS 24.0 — Samsung Galaxy A42 5G (a42xq)

## Highlights

* First build of LineageOS 24.0 for a42xq with SELinux fully enforcing and the ROM signed with private keys.

## Device trees

* a42xq: added the `libshim_samsungaudioparams` shim, fixing in-call audio on the sm7225 platform.
* a42xq: added the nested `vendor/samsung/sm7225-common/a42xq` Soong namespace so the device blobs resolve from the combined vendor repository.
* a42xq: under-display fingerprint geometry (sensor position and radius) is declared to the framework, so the prompt uses the UDFPS UI rather than the generic fallback.

## ROM

* lineage-sdk: LiveDisplay no longer blocks `system_server` at boot, which previously caused a black screen after wiping data.
* SystemUI: the fingerprint prompt message is no longer hidden behind the navigation bar.

## Kernel

* No kernel changes in this release.

## Build and signing

* All APK signing keys and the AVB key used for vbmeta and recovery are private, replacing the public AOSP test keys.
* The first flash over a publicly-keyed build requires wiping data, as the signing keys changed.
