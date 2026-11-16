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

# Google ExtServices for GAPPS builds. The prebuilt com.google.android.extservices
# APEX in /system/apex is not activated (apexd cannot verify it), so
# PackageManagerService aborts system_server with "Required services extension
# package is missing" and the device loops on the boot animation forever.
# Ship the APK as a priv-app fallback plus the APEX public keys.
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/prebuilts/extservices/GoogleExtServices.apk:$(TARGET_COPY_OUT_SYSTEM)/priv-app/GoogleExtServices/GoogleExtServices.apk \
    $(LOCAL_PATH)/prebuilts/extservices/privapp_allowlist_com.google.android.ext.services.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/privapp_allowlist_com.google.android.ext.services.xml \
    $(LOCAL_PATH)/prebuilts/apexkeys/com.android.extservices.avbpubkey:$(TARGET_COPY_OUT_SYSTEM)/etc/security/apex/com.android.extservices.avbpubkey \
    $(LOCAL_PATH)/prebuilts/apexkeys/com.google.android.gmssystem.avbpubkey:$(TARGET_COPY_OUT_SYSTEM)/etc/security/apex/com.google.android.gmssystem.avbpubkey
