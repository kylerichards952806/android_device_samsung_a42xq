#!/usr/bin/env bash
set -euo pipefail

ROOT="${ANDROID_BUILD_TOP:-$(pwd)}"
DEVICE_DIR="$ROOT/device/samsung/a42xq"

if [ ! -f "$ROOT/build/envsetup.sh" ]; then
    echo "run this from the Android source root, or set ANDROID_BUILD_TOP" >&2
    exit 1
fi
if [ -z "${GITHUB_TOKEN:-}" ] && [ -z "${GH_TOKEN:-}" ]; then
    echo "export GITHUB_TOKEN or GH_TOKEN before building" >&2
    exit 1
fi

cd "$ROOT"
# shellcheck disable=SC1091
source build/envsetup.sh
breakfast a42xq
m bacon -j"${JOBS:-2}"

exec "$DEVICE_DIR/tools/publish_release.py" "$@"
