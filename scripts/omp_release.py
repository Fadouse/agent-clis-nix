"""Update Oh My Pi sources from the assets actually published in a stable release."""

import base64
import re


def update_omp_nix(text, release):
    if release["draft"] or release["prerelease"]:
        raise ValueError("Oh My Pi latest release is not stable")
    match = re.fullmatch(r"v([0-9]+\.[0-9]+\.[0-9]+)", release["tag_name"])
    if not match:
        raise ValueError("unexpected Oh My Pi release tag")

    assets = {asset["name"]: asset for asset in release["assets"]}
    text, count = re.subn(r'^  version = "[0-9.]+";$', f'  version = "{match.group(1)}";', text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("cannot locate Oh My Pi version")

    for attribute, name, required in (
        ("src", "omp-linux-x64", True),
        ("licenseFile", "LICENSE", True),
        ("thirdPartyNotices", "THIRD-PARTY-NOTICES.txt", False),
    ):
        asset = assets.get(name)
        if asset is None:
            if required:
                raise ValueError(f"Oh My Pi release is missing required asset: {name}")
            replacement = f"  {attribute} = null;"
        else:
            digest = asset.get("digest")
            if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
                raise ValueError(f"Oh My Pi asset has no valid SHA-256 digest: {name}")
            source_hash = "sha256-" + base64.b64encode(bytes.fromhex(digest[7:])).decode()
            replacement = (
                f"  {attribute} = fetchurl {{\n"
                '    url = "https://github.com/can1357/oh-my-pi/releases/download/v${finalAttrs.version}/' + name + '";\n'
                f'    hash = "{source_hash}";\n'
                "  };"
            )
        pattern = rf"^  {attribute} = (?:null;|fetchurl \{{.*?^  \}};)"
        text, count = re.subn(pattern, lambda _: replacement, text, flags=re.MULTILINE | re.DOTALL)
        if count != 1:
            raise ValueError(f"cannot update Oh My Pi {attribute}")

    return text
