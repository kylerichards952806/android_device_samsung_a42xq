#!/bin/sh
# Rebuild the full GMS APK from the committed parts. GitHub rejects files
# over 100 MB and LFS uploads are blocked on public forks, hence the split.
cd "$(dirname "$0")" || exit 1
[ -f PrebuiltGmsCore.apk ] && exit 0
cat PrebuiltGmsCore.apk.part-* > PrebuiltGmsCore.apk || exit 1
echo "assembled PrebuiltGmsCore.apk ($(wc -c < PrebuiltGmsCore.apk) bytes)"
