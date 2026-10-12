"""Prepare a reproducible npm manifest and lock for an official Pi release."""

import io
import json
import pathlib
import subprocess
import tarfile
import tempfile
import urllib.parse


def generate_lockfile(package_data):
    # Only resolve metadata: never install dependencies or run upstream scripts.
    with tempfile.TemporaryDirectory(prefix="pi-npm-lock-", dir="/tmp") as temporary:
        directory = pathlib.Path(temporary)
        (directory / "package.json").write_text(json.dumps(package_data, indent=2) + "\n")
        try:
            subprocess.run(
                [
                    "npm", "install", "--package-lock-only", "--lockfile-version=3",
                    "--ignore-scripts", "--no-audit", "--no-fund",
                    "--registry=https://registry.npmjs.org/", "--userconfig=/dev/null",
                    "--cache", str(directory / "npm-cache"),
                ],
                cwd=directory,
                check=True,
            )
        except FileNotFoundError as error:
            raise RuntimeError("Pi lock generation requires npm (use Node.js 24)") from error
        return json.loads((directory / "package-lock.json").read_text())


def prepare_pi_npm(archive, version, fetch_json):
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        package_data = json.load(tar.extractfile("package/package.json"))
        if package_data.get("name") != "@earendil-works/pi-coding-agent" or package_data.get("version") != version:
            raise ValueError("Pi package name or version mismatch")
        # The published JavaScript is already built; do not resolve build/test tools.
        package_data.pop("devDependencies", None)
        lock = None
        for name in ("npm-shrinkwrap.json", "package-lock.json"):
            try:
                member = tar.getmember(f"package/{name}")
            except KeyError:
                continue
            lock = json.load(tar.extractfile(member))
            break

    if lock is None:
        print(f"Pi {version} has no upstream npm lock; generating one from official registry metadata", flush=True)
        lock = generate_lockfile(package_data)

    root = lock.get("packages", {}).get("", {})
    if any(record.get("name") != package_data["name"] or record.get("version") != version for record in (lock, root)):
        raise ValueError("Pi npm lock name or version mismatch")

    # Older upstream shrinkwraps omitted integrity for first-party tarballs.
    for key, value in lock["packages"].items():
        if key.startswith("node_modules/@earendil-works/") and value.get("resolved") and not value.get("integrity"):
            name = key.removeprefix("node_modules/")
            metadata = fetch_json(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@')}/{value['version']}")
            value["integrity"] = metadata["dist"]["integrity"]

    return package_data, lock
