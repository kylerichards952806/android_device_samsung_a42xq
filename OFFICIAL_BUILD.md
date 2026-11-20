# a42xq — Official build runbook

Two OFFICIAL variants, one device tree: GAPPS (`WITH_GAPPS=true`) and VANILLA
(`WITH_GAPPS=false`). The only differences are the product package set and the
output names.

## 0. Preconditions

- Infinity-X 17 tree synced with `device/samsung/a42xq` on `infinity-x`.
- `vendor/infinity-priv/keys/` present with the release key set.
- SourceForge upload access for `infinity-x/files/a42xq/` (after approval).
- Clean release build; at minimum `m installclean` when switching variants.

## 1. Signing-key checks

```bash
test -f vendor/infinity-priv/keys/keys.mk
test -f vendor/infinity-priv/keys/releasekey.pk8
test -f vendor/infinity-priv/keys/releasekey.x509.pem

grep -q 'PRODUCT_DEFAULT_DEV_CERTIFICATE := vendor/infinity-priv/keys/releasekey' \
    vendor/infinity-priv/keys/keys.mk

openssl x509 -in vendor/infinity-priv/keys/releasekey.x509.pem \
    -noout -subject -fingerprint -sha256
# Expected SHA-256:
# 7B:9E:24:5F:D9:A6:7C:3B:AC:80:7B:0D:2A:0C:D2:F0:BA:44:DC:40:2A:C6:E1:87:FA:4A:F6:D2:0B:77:61:61
```

The key directory is outside every repo. Back it up off-machine and never
regenerate `releasekey`; changing it breaks OTA updates for existing users.
If the fingerprint differs, stop.

## 2. GAPPS OFFICIAL build

```bash
export INFINITY_BUILD_TYPE=OFFICIAL
export WITH_GAPPS=true
source build/envsetup.sh
lunch infinity_a42xq-user
m bacon
```

Expected output:

`out/target/product/a42xq/Project_Infinity-X-4.2-a42xq-DD.MM.YYYY-GAPPS-OFFICIAL.zip`

The GAPPS build also includes `UpdaterGMSOverlay`, which is only added when
`INFINITY_BUILD_TYPE=OFFICIAL`.

## 3. VANILLA OFFICIAL build

```bash
export INFINITY_BUILD_TYPE=OFFICIAL
export WITH_GAPPS=false
lunch infinity_a42xq-user
m installclean
m bacon
```

`installclean` prevents the GAPPS applications from leaking into the vanilla
product.

Expected output:

`out/target/product/a42xq/Project_Infinity-X-4.2-a42xq-DD.MM.YYYY-VANILLA-OFFICIAL.zip`

## 4. Post-build gates

Run these for both zips before uploading:

```bash
ZIP=out/target/product/a42xq/Project_Infinity-X-4.2-a42xq-DD.MM.YYYY-GAPPS-OFFICIAL.zip

# Filename and build status
basename "$ZIP"
grep -m1 '^ro.infinity.build.status=' out/target/product/a42xq/product/etc/build.prop
grep -m1 '^ro.infinity.buildtype=' out/target/product/a42xq/product/etc/build.prop
grep -m1 '^ro.infinity.maintainer=' out/target/product/a42xq/product/etc/build.prop
grep -m1 '^ro.build.tags=' out/target/product/a42xq/system/build.prop

# OTA certificate must match the release key
unzip -p "$ZIP" META-INF/com/android/otacert | openssl x509 -noout -fingerprint -sha256

# Generated JSON must describe this zip
python3 -m json.tool "$ZIP.json" >/dev/null
```

The zip name must contain `-OFFICIAL`; `ro.infinity.build.status`,
`ro.infinity.buildtype` and `ro.build.tags` must read `OFFICIAL` and
`release-keys`. The `otacert` fingerprint must match step 1.

`bacon` runs `vendor/infinity/build/tools/generate_ota_info.sh` and writes
`$ZIP.json` beside the zip. Its fields are `filename`, `download`, `timestamp`,
`md5`, `size` and `version`. Confirm the JSON's `filename`, `md5` and `size`
match the zip. Do not rename the zip afterwards; the JSON is derived from its
name.

## 5. SourceForge layout

Upload both the zip and its generated `.json` companion to the matching folder:

```text
https://sourceforge.net/projects/infinity-x/files/a42xq/17/gapps/
  Project_Infinity-X-4.2-a42xq-DD.MM.YYYY-GAPPS-OFFICIAL.zip
  Project_Infinity-X-4.2-a42xq-DD.MM.YYYY-GAPPS-OFFICIAL.zip.json

https://sourceforge.net/projects/infinity-x/files/a42xq/17/vanilla/
  Project_Infinity-X-4.2-a42xq-DD.MM.YYYY-VANILLA-OFFICIAL.zip
  Project_Infinity-X-4.2-a42xq-DD.MM.YYYY-VANILLA-OFFICIAL.zip.json
```

The `.json` files generated next to the zips already contain the correct
SourceForge download URL. The Updater does not read them from SourceForge; it
reads the copies committed to `official_devices`.

## 6. official_devices files

Open a PR against `ProjectInfinity-X/official_devices`, branch `17`, adding or
updating:

- `devices/a42xq.json` — maintainer card:
  `maintainer`, `maintainerurl`, `devicemodel`, `codename`, `supportgroupurl`,
  `donateurl1`, `donateurl2`.
- `gapps/a42xq.json` — the exact contents of the GAPPS `<zip>.json`.
- `vanilla/a42xq.json` — the exact contents of the VANILLA `<zip>.json`.
- `changelog/a42xq.txt` — the device changelog shown by the Updater.
- `deviceimages/a42xq.webp` — device image for the official devices page.

Updater endpoints after merge:

```text
https://raw.githubusercontent.com/ProjectInfinity-X/official_devices/17/gapps/a42xq.json
https://raw.githubusercontent.com/ProjectInfinity-X/official_devices/17/vanilla/a42xq.json
```

Until those two files exist, `Updater` reports missing OTA info even on a
correctly signed OFFICIAL build.

## 7. Release checklist

- [ ] Release-key fingerprint matches step 1.
- [ ] Both zips are named `-OFFICIAL`.
- [ ] Both `otacert` fingerprints match the release key.
- [ ] `ro.infinity.build.status=OFFICIAL` and `ro.build.tags=release-keys`.
- [ ] Both `<zip>.json` files validate and match the zips.
- [ ] Both zips and `.json` companions are in the correct SourceForge folders.
- [ ] `official_devices` PR includes the device card, both OTA JSONs, changelog
      and device image.
- [ ] PR merged; both raw JSON URLs return 200.
