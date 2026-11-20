# Infinity-X 4.2 (Android 17) — Galaxy A42 5G (a42xq)

Branch `infinity-x` carries the Infinity-X product configuration for the
Samsung Galaxy A42 5G (SM-A426B, codename `a42xq`), layered on top of the
LineageOS 24.0 device tree.

## Variants

`WITH_GAPPS` selects the variant. Infinity-X defaults to GAPPS.

```bash
export WITH_GAPPS=true     # GAPPS
export WITH_GAPPS=false    # VANILLA
```

## Build

```bash
source build/envsetup.sh
lunch infinity_a42xq-user
m bacon
```

`bacon` writes the ROM zip and its OTA JSON to `out/target/product/a42xq/`.

The vanilla variant needs `m installclean` between the two builds, because the
installed GAPPS applications otherwise leak into the vanilla product.

## Official build

Official builds are the same target built with `INFINITY_BUILD_TYPE=OFFICIAL`.
It defaults to `UNOFFICIAL`; without the export the zip is named `-UNOFFICIAL`
and `UpdaterGMSOverlay` is not included in the GAPPS build.

```bash
export INFINITY_BUILD_TYPE=OFFICIAL
export WITH_GAPPS=true
source build/envsetup.sh
lunch infinity_a42xq-user
m bacon
```

Build the vanilla variant in a clean tree as well:

```bash
export INFINITY_BUILD_TYPE=OFFICIAL
export WITH_GAPPS=false
m installclean
m bacon
```

### Signing

Official builds sign with the private keys in `vendor/infinity-priv/keys/`.
`vendor/infinity/config/common.mk` includes `keys/keys.mk` unconditionally for
`OFFICIAL`, so a missing key directory fails the build instead of silently
falling back to test keys. `keys.mk` sets:

```
PRODUCT_DEFAULT_DEV_CERTIFICATE := vendor/infinity-priv/keys/releasekey
```

The key directory is not part of any repo. Back it up off-machine and never
regenerate `releasekey`: every official OTA must be signed with the same
certificate or the updater will refuse to install it.

### OTA publishing

`bacon` runs `vendor/infinity/build/tools/generate_ota_info.sh`, which writes
`<zip>.json` next to the zip with `filename`, `download`, `timestamp`, `md5`,
`size` and `version`. Do not rename the zip after the build; the JSON is
derived from that filename.

1. Upload the OFFICIAL zip and its `.json` to SourceForge:
   - `https://sourceforge.net/projects/infinity-x/files/a42xq/17/gapps/`
   - `https://sourceforge.net/projects/infinity-x/files/a42xq/17/vanilla/`
2. Add or update the matching files in
   `ProjectInfinity-X/official_devices` branch `17`:
   - `gapps/a42xq.json` and `vanilla/a42xq.json` (contents of the generated
     `<zip>.json`)
   - `devices/a42xq.json` (maintainer, device model, support group and donate
     links)
   - `changelog/a42xq.txt`
   - `deviceimages/a42xq.webp`
3. The Updater reads
   `https://raw.githubusercontent.com/ProjectInfinity-X/official_devices/17/{gapps,vanilla}/a42xq.json`.
   Until those files are merged, the Updater reports missing OTA info.

## Device

- Maintainer: `kyler084`
- Kernel: `4.19.325-kyler084-a42tweak-v1.0.2`, KernelSU-Next, no SUSFS
- IMS/VoLTE preserved through `generic-ims`
- About phone: Galaxy A42 5G, Snapdragon 750G, 720 x 1600 60 Hz, 5000 mAh,
  48MP + 8MP + 5MP + 5MP

## Notes

The `a42xq` blob namespace is nested inside the combined `sm7225-common`
vendor repository, hence the extra `PRODUCT_SOONG_NAMESPACES` entry in
`infinity_a42xq.mk`.
