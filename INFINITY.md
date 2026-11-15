# Infinity-X 4.2 (Android 17) — Galaxy A42 5G (a42xq)

Branch `infinity-x` carries the Infinity-X product configuration for the
Samsung Galaxy A42 5G (SM-A426B, codename `a42xq`), layered on top of the
LineageOS 24.0 device tree.

## Variants

`WITH_GAPPS` selects the variant. Infinity-X defaults to GAPPS.

```
export WITH_GAPPS=true     # GAPPS
export WITH_GAPPS=false    # VANILLA
```

## Build

```
source build/envsetup.sh
lunch infinity_a42xq-user
m bacon
```

The vanilla variant needs `m installclean` between the two builds, because the
installed GAPPS applications otherwise leak into the vanilla product.

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
