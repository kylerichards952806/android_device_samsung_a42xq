#!/bin/sh
# Rebuild the full GMS APK from the committed parts. GitHub rejects files
# over 100 MB and LFS uploads are blocked on public forks, hence the split.
# The result is checksum-verified and only moved into place after it matches.
set -eu
cd "$(dirname "$0")" || exit 1
out=PrebuiltGmsCore.apk
sum=PrebuiltGmsCore.apk.sha256

want=$(cat "$sum")
if [ -f "$out" ]; then
    have=$(sha256sum "$out" | cut -d' ' -f1)
    [ "$have" = "$want" ] && exit 0
    echo "PrebuiltGmsCore.apk has wrong checksum, reassembling" >&2
fi

tmp="$out.tmp.$$"
trap 'rm -f "$tmp"' EXIT INT TERM HUP

cat PrebuiltGmsCore.apk.part-* > "$tmp" || exit 1
got=$(sha256sum "$tmp" | cut -d' ' -f1)
if [ "$got" != "$want" ]; then
    echo "ERROR: assembled GMS APK checksum mismatch" >&2
    echo "  expected $want" >&2
    echo "  got      $got" >&2
    exit 1
fi
mv "$tmp" "$out"
trap - EXIT INT TERM HUP
echo "assembled PrebuiltGmsCore.apk ($(wc -c < "$out") bytes, sha256 $want)"
