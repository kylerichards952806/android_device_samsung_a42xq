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

include device/samsung/sm7225-common/BoardConfigCommon.mk

# Device-specific SELinux rules (rild diag, NFC property reads)
BOARD_VENDOR_SEPOLICY_DIRS += $(LOCAL_PATH)/sepolicy/vendor

# Kernel
TARGET_KERNEL_CONFIG        := vendor/a42xq_eur_open_defconfig
BOARD_NAME                  := SRPTF23D003

# Camera
$(call soong_config_set,samsungCameraVars,extra_ids,50,54) # ID=50 is depth camera and ID=54 is macro

# Display
TARGET_SCREEN_DENSITY := 300

# OTA assert
TARGET_OTA_ASSERT_DEVICE := a42xq

# Dynamic partitions
# The A42 5G super partition (/dev/block/by-name/super -> sda27) is
# 9,017,753,600 bytes. The shared sm7225 configuration assumes
# 10,385,096,704, which let the GAPPS system/product images grow past
# what the device can actually hold. Pin the super and the four logical
# partitions here so sm7225-common keeps its values for other devices.
#   system 5,472,002,048 + vendor 1,138,327,552 + product 2,200,674,304
#   + odm 52,510,720 = 8,863,514,624, which fits the 9,013,559,296 group.
BOARD_SUPER_PARTITION_SIZE                 := 9017753600
BOARD_SAMSUNG_DYNAMIC_PARTITIONS_SIZE      := 9013559296 # BOARD_SUPER_PARTITION_SIZE - 4 MiB
BOARD_SYSTEMIMAGE_PARTITION_SIZE           := 5472002048
# sm7225-common still defines a reserved size for the shared tree; the
# explicit size above replaces it and the build rejects both.
BOARD_SYSTEMIMAGE_PARTITION_RESERVED_SIZE   :=
BOARD_VENDORIMAGE_PARTITION_SIZE           := 1138327552
BOARD_PRODUCTIMAGE_PARTITION_SIZE          := 2200674304
BOARD_ODMIMAGE_PARTITION_SIZE              := 52510720
