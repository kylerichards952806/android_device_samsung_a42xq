# Publishing ROM releases

`tools/publish_release.py` uploads a finished `lineage-24.0-*-UNOFFICIAL-a42xq.zip` to the GitHub Releases page, with its changelog, size and SHA-256.

It refuses to publish unless the OTA certificate inside the zip matches the current private release key (`vendor/lineage-priv/keys/releasekey.x509.pem`). Builds signed with the public test key or an older private key are rejected, so they cannot break updates for users.

## Requirements

* Python 3
* `openssl`
* `GITHUB_TOKEN` or `GH_TOKEN` with `repo` (or `public_repo`) scope, or a Git
  credential helper that can return the GitHub token

Never commit the token. Export it in the shell or provide it through your secret manager. If no token is exported, pass `--credential-helper /root/gcm-helper.sh` (the WSL build script does this automatically).

## After a successful build

From the Android source root:

```bash
export GITHUB_TOKEN=...
device/samsung/a42xq/tools/publish_release.py
```

The script picks the newest zip in `out/target/product/a42xq`, verifies the release key, computes the SHA-256, creates the release and uploads the asset. The tag is `lineage-24.0-YYYYMMDD` and the release is marked latest.

Useful options:

```bash
# Use a changelog file written for this build
device/samsung/a42xq/tools/publish_release.py --notes-file notes-20261115.md

# Extract the matching "**Changelog — DD/MM/YYYY**" section from the XDA post
device/samsung/a42xq/tools/publish_release.py --release-post /path/to/release-post-a42xq-24.0.md

# Verify everything without touching GitHub
device/samsung/a42xq/tools/publish_release.py --dry-run

# Backfill an older build without moving the "Latest" badge
device/samsung/a42xq/tools/publish_release.py --zip out/.../old.zip --no-latest
```

The publisher is idempotent: if the release and asset already exist with the same size and digest, it exits successfully. If a previous upload left a draft with the asset, rerunning finishes publishing that draft.

## Build and publish in one command

`tools/build-and-release.sh` runs `breakfast a42xq`, `m bacon -j2`, then the publisher:

```bash
export GITHUB_TOKEN=...
device/samsung/a42xq/tools/build-and-release.sh --notes-file notes-20261115.md
```

Set `JOBS=4` to override the build job count.

The local WSL scripts `/root/android/build-j25.sh`, `run-build-j2.sh`,
`run-build-j4.sh` and `run-build-j6.sh` are wired through
`/root/android/publish-after-build.sh` to publish after a successful build. They
use `/root/gcm-helper.sh` when no token is exported, and read the XDA release
post from `/mnt/c/a42/release-post-a42xq-24.0.md` by default. Override that path
with `RELEASE_POST=/path/to/post.md`.
