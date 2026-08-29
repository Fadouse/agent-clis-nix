#!/usr/bin/env python3
import base64
import hashlib
import io
import json
import os
import pathlib
import re
import tarfile
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEADERS = {"User-Agent": "Fadouse-agent-clis-updater"}
if token := os.environ.get("GH_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {token}"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch(url))


def sri_bytes(data: bytes) -> str:
    return "sha256-" + base64.b64encode(hashlib.sha256(data).digest()).decode()


def sri_hex(value: str) -> str:
    return "sha256-" + base64.b64encode(bytes.fromhex(value.removeprefix("sha256:"))).decode()


def replace_version_hash(path: pathlib.Path, version: str, source_hash: str):
    text = path.read_text()
    old = re.search(r'  version = "([0-9A-Za-z.-]+)";', text)
    if not old:
        raise SystemExit(f"cannot locate version in {path}")
    if old.group(1) == version:
        return False
    text = text.replace(old.group(0), f'  version = "{version}";', 1)
    text, count = re.subn(r'    hash = "sha256-[A-Za-z0-9+/=]+";', f'    hash = "{source_hash}";', text, count=1)
    if count != 1:
        raise SystemExit(f"cannot update source hash in {path}")
    path.write_text(text)
    print(f"updated {path.name}: {old.group(1)} -> {version}")
    return True


# Claude Code: official npm version points to the matching official native manifest.
claude_meta = fetch_json("https://registry.npmjs.org/@anthropic-ai/claude-code/latest")
claude_version = claude_meta["version"]
claude_manifest = fetch_json(f"https://downloads.claude.ai/claude-code-releases/{claude_version}/manifest.json")
if claude_manifest["version"] != claude_version:
    raise SystemExit("Claude manifest version mismatch")
claude_changed = replace_version_hash(
    ROOT / "packages/claude-code.nix",
    claude_version,
    sri_hex(claude_manifest["platforms"]["linux-x64"]["checksum"]),
)
if claude_changed:
    platform_meta = fetch_json(f"https://registry.npmjs.org/@anthropic-ai/claude-code-linux-x64/{claude_version}")
    platform_archive = fetch(platform_meta["dist"]["tarball"])
    with tarfile.open(fileobj=io.BytesIO(platform_archive), mode="r:gz") as tar:
        license_text = tar.extractfile("package/LICENSE.md").read()
    (ROOT / "packages/claude-code.LICENSE.md").write_bytes(license_text)

# Codex: official stable GitHub release and official asset digest.
codex_release = fetch_json("https://api.github.com/repos/openai/codex/releases/latest")
if codex_release["draft"] or codex_release["prerelease"]:
    raise SystemExit("Codex latest release is not stable")
codex_match = re.fullmatch(r"rust-v([0-9]+\.[0-9]+\.[0-9]+)", codex_release["tag_name"])
if not codex_match:
    raise SystemExit("unexpected Codex release tag")
codex_asset = next(a for a in codex_release["assets"] if a["name"] == "codex-package-x86_64-unknown-linux-musl.tar.gz")
replace_version_hash(ROOT / "packages/codex.nix", codex_match.group(1), sri_hex(codex_asset["digest"]))

# Oh My Pi: official stable GitHub release assets and their official digests.
omp_release = fetch_json("https://api.github.com/repos/can1357/oh-my-pi/releases/latest")
if omp_release["draft"] or omp_release["prerelease"]:
    raise SystemExit("Oh My Pi latest release is not stable")
omp_match = re.fullmatch(r"v([0-9]+\.[0-9]+\.[0-9]+)", omp_release["tag_name"])
if not omp_match:
    raise SystemExit("unexpected Oh My Pi release tag")
omp_assets = {asset["name"]: asset for asset in omp_release["assets"]}
omp_path = ROOT / "packages/oh-my-pi.nix"
omp_text = omp_path.read_text()
omp_current = re.search(r'  version = "([0-9.]+)";', omp_text).group(1)
if omp_current != omp_match.group(1):
    omp_text = omp_text.replace(f'  version = "{omp_current}";', f'  version = "{omp_match.group(1)}";', 1)
    for attribute, name in [("src", "omp-linux-x64"), ("licenseFile", "LICENSE"), ("thirdPartyNotices", "THIRD-PARTY-NOTICES.txt")]:
        pattern = rf'({attribute} = fetchurl \{{.*?hash = ")[^"]+(";)'
        omp_text, count = re.subn(pattern, rf'\g<1>{sri_hex(omp_assets[name]["digest"])}\g<2>', omp_text, count=1, flags=re.DOTALL)
        if count != 1:
            raise SystemExit(f"cannot update Oh My Pi {attribute}")
    omp_path.write_text(omp_text)
    print(f"updated oh-my-pi.nix: {omp_current} -> {omp_match.group(1)}")

# Pi: official npm release, official tarball, and official registry integrity for omitted first-party SRI fields.
pi_meta = fetch_json("https://registry.npmjs.org/@earendil-works/pi-coding-agent/latest")
pi_version = pi_meta["version"]
pi_nix = ROOT / "packages/pi-coding-agent.nix"
pi_current = re.search(r'  version = "([0-9.]+)";', pi_nix.read_text()).group(1)
if pi_current != pi_version:
    archive = fetch(pi_meta["dist"]["tarball"])
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        package_json = tar.extractfile("package/package.json").read()
        shrinkwrap = json.load(tar.extractfile("package/npm-shrinkwrap.json"))
    package_data = json.loads(package_json)
    if package_data["version"] != pi_version:
        raise SystemExit("Pi package version mismatch")
    package_data.pop("devDependencies", None)
    package_json = (json.dumps(package_data, indent=2) + "\n").encode()
    for key, value in shrinkwrap["packages"].items():
        if key.startswith("node_modules/@earendil-works/") and value.get("resolved") and not value.get("integrity"):
            name = key.removeprefix("node_modules/")
            metadata = fetch_json(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@')}/{value['version']}")
            value["integrity"] = metadata["dist"]["integrity"]
    (ROOT / "packages/pi-coding-agent.package.json").write_bytes(package_json + b"\n")
    (ROOT / "packages/pi-coding-agent.npm-shrinkwrap.json").write_text(json.dumps(shrinkwrap, indent=2) + "\n")
    text = pi_nix.read_text().replace(f'  version = "{pi_current}";', f'  version = "{pi_version}";', 1)
    text, count = re.subn(r'    hash = "sha256-[A-Za-z0-9+/=]+";', f'    hash = "{sri_bytes(archive)}";', text, count=1)
    if count != 1:
        raise SystemExit("cannot update Pi source hash")
    text = re.sub(r'  npmDepsHash = "sha256-[A-Za-z0-9+/=]+";', '  npmDepsHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";', text, count=1)
    pi_nix.write_text(text)
    print(f"updated pi-coding-agent.nix: {pi_current} -> {pi_version}")
