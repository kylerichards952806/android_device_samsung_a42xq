#
# Copyright (C) 2021 The LineageOS Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

LOCAL_PATH := device/samsung/a42xq

DEVICE_PACKAGE_OVERLAYS += \
    $(LOCAL_PATH)/overlay \
    $(LOCAL_PATH)/overlay-lineage

# call the common setup
$(call inherit-product, device/samsung/sm7225-common/common.mk)

# call the proprietary setup
$(call inherit-product, vendor/samsung/a42xq/a42xq-vendor.mk)

# Init files
PRODUCT_PACKAGES += \
    init.a42xq.rc

# Audio
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/audio/mixer_paths.xml:$(TARGET_COPY_OUT_VENDOR)/etc/mixer_paths.xml

PRODUCT_PACKAGES += libshim_samsungaudioparams

# The device tree declares its own Soong namespace, so register it with the
# product. Without this entry the modules in prebuilts/Android.bp are not
# visible to PRODUCT_PACKAGES, and a name like GoogleExtServices resolves to
# the empty dummy app in vendor/pixel/gms/dummy-apps instead.
PRODUCT_SOONG_NAMESPACES += device/samsung/a42xq

# Google ExtServices for GAPPS builds. The prebuilt com.google.android.extservices
# APEX in /system/apex is not activated (apexd cannot verify it), so
# PackageManagerService aborts system_server with "Required services extension
# package is missing" and the device loops on the boot animation forever.
# Ship the APK as a priv-app fallback plus the APEX public keys.
ifeq ($(WITH_GAPPS),true)
PRODUCT_PACKAGES += A42xqExtServices
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/prebuilts/extservices/privapp_allowlist_com.google.android.ext.services.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/privapp_allowlist_com.google.android.ext.services.xml \

# Google Play services fallback. The GMS APEX (com.google.android.gmssystem.prodvic.apex)
# is copied to /system/apex by vendor/pixel/gms, but apexd never activates it on
# this device, so com.google.android.gms was missing entirely and Play Store
# crashed with "Failed to find provider com.google.android.gsf.gservices".
# Ship the APK extracted from that APEX (26.11.36) as a privileged app. If
# apexd ever starts mounting the APEX, drop this copy to avoid a duplicate.
# GitHub rejects files over 100 MB and blocks LFS on public forks, so the APK
# is committed as prebuilts/gms/PrebuiltGmsCore.apk.part-* and assembled here.
GMS_ASSEMBLED := $(shell $(LOCAL_PATH)/prebuilts/gms/assemble.sh >&2)
PRODUCT_PACKAGES += A42xqGmsCore

PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/prebuilts/gms/privapp_allowlist_com.google.android.gmssystem.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/privapp_allowlist_com.google.android.gmssystem.xml \
    $(LOCAL_PATH)/prebuilts/gms/preinstalled_packages_com.google.android.gmssystem.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/sysconfig/preinstalled_packages_com.google.android.gmssystem.xml

endif # WITH_GAPPS

# Drop the GMS APEX. Play services ships as the PrebuiltGmsCore priv-app
# fallback above; if apexd ever starts activating com.google.android.gmssystem
# .prodvic.apex too, two packages named com.google.android.gms would be scanned.
PRODUCT_PACKAGES := $(filter-out com.google.android.gmssystem.prodvic,$(PRODUCT_PACKAGES))
PRODUCT_COPY_FILES := $(filter-out %com.google.android.gmssystem.prodvic.apex%,$(PRODUCT_COPY_FILES))

# Google ExtServices ships as the priv-app APK fallback above, so drop its APEX
# from the image too. Both Google APEXes are left inactive by apexd on this
# device (payload is byte-identical to the prebuilt and the avbpubkey matches,
# cause still unknown), and shipping them only risks a duplicate package.
PRODUCT_PACKAGES := $(filter-out com.google.android.extservices,$(PRODUCT_PACKAGES))

# Google SetupWizard is enabled in optional mode: it now advances normally on
# this port, so first boot runs the wizard like a stock GApps build.
PRODUCT_PROPERTY_OVERRIDES += ro.setupwizard.mode=OPTIONAL

