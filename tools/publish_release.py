#!/usr/bin/env python3
"""Publish a release-key-signed LineageOS build to GitHub Releases.

The build is only published when META-INF/com/android/otacert matches the
private release key used by the current builds. The SHA-256 is computed
locally, printed, stored in the release notes, and compared with the digest
reported by GitHub after upload.

Usage:
    export GITHUB_TOKEN=...          # token with repo/public_repo scope
    tools/publish_release.py         # newest out/.../lineage-*.zip
    tools/publish_release.py --notes-file notes.md
    tools/publish_release.py --release-post release-post-a42xq-24.0.md
    tools/publish_release.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.client
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_REPO = "kylerichards952806/android_device_samsung_a42xq"
DEFAULT_PRODUCT = "a42xq"
DEFAULT_CHANGELOG = (
    "https://github.com/kylerichards952806/"
    "android_device_samsung_sm7225-common/blob/lineage-24.0/CHANGELOG.md"
)
API = "https://api.github.com"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, help="ROM zip; defaults to the newest build")
    parser.add_argument("--android-root", type=Path, help="Android source root")
    parser.add_argument("--product", default=DEFAULT_PRODUCT)
    parser.add_argument("--version", help="YYYYMMDD; defaults to the zip filename")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--tag", help="release tag; defaults to lineage-24.0-<version>")
    parser.add_argument("--title", help="release title")
    parser.add_argument("--target", default="lineage-24.0", help="release target branch")
    parser.add_argument("--notes", help="release changelog text")
    parser.add_argument("--notes-file", type=Path, help="file containing the changelog")
    parser.add_argument("--release-post", type=Path,
                        help="XDA post; extracts the matching **Changelog — DD/MM/YYYY** section")
    parser.add_argument("--release-key-cert", type=Path,
                        help="releasekey.x509.pem; defaults to vendor/lineage-priv/keys")
    parser.add_argument("--changelog-url", default=DEFAULT_CHANGELOG)
    parser.add_argument("--latest", dest="latest", action="store_true", default=True)
    parser.add_argument("--no-latest", dest="latest", action="store_false")
    parser.add_argument("--prerelease", action="store_true")
    parser.add_argument("--draft", action="store_true", help="leave the release as a draft")
    parser.add_argument("--dry-run", action="store_true", help="verify and print without uploading")
    return parser.parse_args()


def android_root(args):
    if args.android_root:
        return args.android_root.resolve()
    env = os.environ.get("ANDROID_BUILD_TOP")
    if env:
        return Path(env).resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "build" / "envsetup.sh").is_file():
            return parent
    raise SystemExit("cannot find the Android root; set ANDROID_BUILD_TOP or pass --android-root")


def newest_zip(root, product):
    out = root / "out" / "target" / "product" / product
    pattern = "lineage-24.0-*-UNOFFICIAL-%s.zip" % product
    version_pattern = re.compile(r"lineage-24\.0-(\d{8})-UNOFFICIAL-%s\.zip$" % re.escape(product))
    candidates = [path for path in out.glob(pattern) if path.is_file()]
    if not candidates:
        raise SystemExit("no %s found in %s" % (pattern, out))

    def version_key(path):
        match = version_pattern.search(path.name)
        return (match.group(1) if match else "", path.stat().st_mtime)

    return max(candidates, key=version_key)


def parse_version(zip_path, product, explicit):
    if explicit:
        version = explicit
    else:
        match = re.search(r"lineage-24\.0-(\d{8})-UNOFFICIAL-%s\.zip$" % re.escape(product),
                          zip_path.name)
        if not match:
            raise SystemExit("cannot read a YYYYMMDD version from " + zip_path.name)
        version = match.group(1)
    if not re.fullmatch(r"\d{8}", version):
        raise SystemExit("version must be YYYYMMDD")
    try:
        dt.datetime.strptime(version, "%Y%m%d")
    except ValueError:
        raise SystemExit("invalid build date " + version)
    return version


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def certificate_der(path, data=None):
    if data is None:
        data = Path(path).read_bytes()
    if b"BEGIN CERTIFICATE" in data:
        inform = "PEM"
    else:
        inform = "DER"
    source = path
    temporary = None
    if data is not None and not isinstance(data, (str, os.PathLike)):
        temporary = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
        temporary.write(data)
        temporary.close()
        source = temporary.name
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".der")
    output.close()
    output_path = output.name
    try:
        result = subprocess.run(
            ["openssl", "x509", "-inform", inform, "-in", str(source),
             "-outform", "DER", "-out", output_path],
            capture_output=True,
        )
        if result.returncode != 0:
            raise SystemExit("cannot parse certificate %s: %s" %
                             (path, result.stderr.decode(errors="replace").strip()))
        return Path(output_path).read_bytes()
    finally:
        if temporary is not None:
            os.unlink(temporary.name)
        os.unlink(output_path)


def fingerprint(der):
    temporary = tempfile.NamedTemporaryFile(delete=False, suffix=".der")
    temporary.write(der)
    temporary.close()
    try:
        result = subprocess.run(
            ["openssl", "x509", "-inform", "DER", "-in", temporary.name,
             "-noout", "-fingerprint", "-sha256"],
            capture_output=True, check=True,
        )
        return result.stdout.decode().strip().split("=", 1)[-1]
    finally:
        os.unlink(temporary.name)


def verify_release_key(zip_path, key_path):
    if not key_path.is_file():
        raise SystemExit("release key certificate not found: " + str(key_path))
    with zipfile.ZipFile(zip_path) as package:
        try:
            ota_cert = package.read("META-INF/com/android/otacert")
        except KeyError:
            raise SystemExit("zip has no META-INF/com/android/otacert")
    expected = certificate_der(key_path)
    actual = certificate_der("<META-INF/com/android/otacert>", ota_cert)
    expected_fp = fingerprint(expected)
    actual_fp = fingerprint(actual)
    if actual != expected:
        raise SystemExit(
            "refusing to publish: OTA is signed with %s, expected release key %s"
            % (actual_fp, expected_fp)
        )
    print("release key verified:", actual_fp, flush=True)


def notes_from_post(path, version):
    date = dt.datetime.strptime(version, "%Y%m%d").date()
    marker = "**Changelog — %d/%02d/%d**" % (date.day, date.month, date.year)
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    start = text.find(marker)
    if start < 0:
        raise SystemExit("no %s section in %s" % (marker, path))
    body = text[start + len(marker):]
    end = len(body)
    for heading in ("\n**Changelog —", "\n**LineageOS changes**", "\n**Installation**",
                    "\n**Sources**", "\n**Credits**"):
        position = body.find(heading)
        if 0 <= position < end:
            end = position
    return body[:end].strip()


def release_body(version, zip_path, size, digest, notes, changelog_url):
    date = dt.datetime.strptime(version, "%Y%m%d").date()
    pretty_date = "%d %s %d" % (date.day, date.strftime("%B"), date.year)
    if not notes:
        notes = "See the [cumulative changelog](%s)." % changelog_url
    return """**LineageOS 24.0 for the Samsung Galaxy A42 5G (a42xq) — %s**

This build is signed with the current private a42xq release key.

**Changelog**

%s

**Download**

* `%s`
* Size: %s bytes
* SHA-256: `%s`

**Notes**

* Clean flash (Format Data) is required when coming from a build signed with a different key.
* Full cumulative changelog: [CHANGELOG.md](%s)
""" % (pretty_date, notes, zip_path.name, "{:,}".format(size), digest, changelog_url)


def credential():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN or GH_TOKEN to a token with repo/public_repo scope")
    return token


def api(method, path, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "token " + token,
        "User-Agent": "a42xq-release-publisher",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        try:
            body = json.loads(body).get("message", body)
        except Exception:
            pass
        return error.code, {"message": body}


def find_release(repo, tag, token):
    status, result = api("GET", "/repos/%s/releases/tags/%s" % (repo, tag), token)
    if status == 200:
        return result
    if status == 404:
        return None
    raise SystemExit("cannot read release %s: %s %s" % (tag, status, result.get("message")))


def upload_asset(upload_url, token, path, name):
    size = path.stat().st_size
    parsed = urllib.parse.urlparse(upload_url.split("{")[0])
    target = parsed.path + "?" + urllib.parse.urlencode({"name": name})
    connection = http.client.HTTPSConnection("uploads.github.com", timeout=3600)
    try:
        connection.putrequest("POST", target)
        connection.putheader("Accept", "application/vnd.github+json")
        connection.putheader("Authorization", "token " + token)
        connection.putheader("Content-Type", "application/zip")
        connection.putheader("Content-Length", str(size))
        connection.putheader("User-Agent", "a42xq-release-publisher")
        connection.endheaders()
        sent = 0
        reported = 0
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(4 * 1024 * 1024)
                if not chunk:
                    break
                connection.send(chunk)
                sent += len(chunk)
                if sent - reported >= 128 * 1024 * 1024:
                    print("  uploaded %d / %d MB" % (sent // (1024 * 1024), size // (1024 * 1024)),
                          flush=True)
                    reported = sent
        response = connection.getresponse()
        payload = response.read()
        if response.status not in (200, 201):
            raise SystemExit("asset upload failed: %s %s" % (response.status, payload[:500]))
        return json.loads(payload)
    finally:
        connection.close()


def main():
    args = parse_args()
    root = android_root(args)
    zip_path = args.zip.resolve() if args.zip else newest_zip(root, args.product)
    version = parse_version(zip_path, args.product, args.version)
    tag = args.tag or "lineage-24.0-" + version
    title = args.title or "LineageOS 24.0 — %d %s %d" % (
        dt.datetime.strptime(version, "%Y%m%d").day,
        dt.datetime.strptime(version, "%Y%m%d").strftime("%B"),
        dt.datetime.strptime(version, "%Y%m%d").year,
    )
    key_path = args.release_key_cert or (
        root / "vendor" / "lineage-priv" / "keys" / "releasekey.x509.pem"
    )
    digest = sha256(zip_path)
    size = zip_path.stat().st_size
    print("zip:", zip_path)
    print("size:", size, "bytes")
    print("sha256:", digest)
    verify_release_key(zip_path, key_path)

    notes = args.notes
    if notes is None and args.notes_file:
        notes = args.notes_file.read_text(encoding="utf-8").strip()
    if notes is None and args.release_post:
        notes = notes_from_post(args.release_post, version)
    body = release_body(version, zip_path, size, digest, notes, args.changelog_url)

    if args.dry_run:
        print(json.dumps({
            "repo": args.repo,
            "tag": tag,
            "title": title,
            "target": args.target,
            "latest": args.latest,
            "prerelease": args.prerelease,
            "asset": zip_path.name,
            "size": size,
            "sha256": digest,
            "body": body,
        }, indent=2))
        return

    token = credential()
    status, repo = api("GET", "/repos/" + args.repo, token)
    if status != 200:
        raise SystemExit("cannot read repo: %s %s" % (status, repo.get("message")))
    if not repo.get("permissions", {}).get("push"):
        raise SystemExit("token does not have push access to " + args.repo)

    existing = find_release(args.repo, tag, token)
    uploaded = None
    if existing:
        print("release exists:", existing["html_url"])
        release_id = existing["id"]
        upload_url = existing["upload_url"]
        for asset in existing.get("assets", []):
            if asset.get("name") != zip_path.name:
                continue
            if asset.get("size") != size:
                raise SystemExit("existing asset has a different size; refusing to overwrite")
            if asset.get("digest") and asset["digest"] != "sha256:" + digest:
                raise SystemExit("existing asset has a different digest; refusing to overwrite")
            if not existing.get("draft"):
                print("asset already published:", asset["browser_download_url"])
                return
            print("asset already uploaded to draft; finishing the release", flush=True)
            uploaded = asset
    else:
        payload = {
            "tag_name": tag,
            "target_commitish": args.target,
            "name": title,
            "body": body,
            "draft": True,
            "prerelease": args.prerelease,
            "make_latest": "true" if args.latest else "false",
        }
        status, existing = api("POST", "/repos/%s/releases" % args.repo, token, payload)
        if status not in (200, 201):
            raise SystemExit("release creation failed: %s %s" % (status, existing.get("message")))
        release_id = existing["id"]
        upload_url = existing["upload_url"]
        print("draft release created:", release_id)

    if uploaded is None:
        print("uploading", zip_path.name, size, "bytes", flush=True)
        uploaded = upload_asset(upload_url, token, zip_path, zip_path.name)
        if uploaded.get("size") != size:
            raise SystemExit("uploaded asset size mismatch: %s" % uploaded.get("size"))
        if uploaded.get("digest") and uploaded["digest"] != "sha256:" + digest:
            raise SystemExit("uploaded asset digest mismatch: %s" % uploaded.get("digest"))
        print("asset uploaded:", uploaded.get("browser_download_url"), flush=True)

    if not args.draft:
        status, published = api(
            "PATCH",
            "/repos/%s/releases/%s" % (args.repo, release_id),
            token,
            {"draft": False, "make_latest": "true" if args.latest else "false"},
        )
        if status != 200:
            raise SystemExit("release publish failed: %s %s" % (status, published.get("message")))
        print("published:", published["html_url"])


if __name__ == "__main__":
    main()
