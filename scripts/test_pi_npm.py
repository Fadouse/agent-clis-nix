import copy
import io
import json
import pathlib
import subprocess
import tarfile
import unittest
from unittest.mock import Mock, patch

from pi_npm import prepare_pi_npm


class PiNpmTests(unittest.TestCase):
    def setUp(self):
        self.package = {
            "name": "@earendil-works/pi-coding-agent",
            "version": "1.1.0",
            "dependencies": {"chalk": "6.0.0"},
            "devDependencies": {"vitest": "4.0.0"},
            "scripts": {"postinstall": "exit 1"},
        }
        self.lock = {
            "name": self.package["name"],
            "version": self.package["version"],
            "lockfileVersion": 3,
            "packages": {
                "": {"name": self.package["name"], "version": self.package["version"]},
                "node_modules/chalk": {"version": "6.0.0", "integrity": "sha512-existing"},
            },
        }
        self.fetch_json = Mock(side_effect=AssertionError("unexpected network request"))

    def archive(self, files):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            for name, data in {"package.json": self.package, **files}.items():
                encoded = json.dumps(data).encode()
                member = tarfile.TarInfo(f"package/{name}")
                member.size = len(encoded)
                tar.addfile(member, io.BytesIO(encoded))
        return buffer.getvalue()

    def test_preserves_upstream_shrinkwrap(self):
        with patch("pi_npm.subprocess.run") as run:
            package, lock = prepare_pi_npm(self.archive({"npm-shrinkwrap.json": self.lock}), "1.1.0", self.fetch_json)
        self.assertNotIn("devDependencies", package)
        self.assertEqual(package["dependencies"], self.package["dependencies"])
        self.assertEqual(lock, self.lock)
        run.assert_not_called()

    def test_accepts_package_lock(self):
        with patch("pi_npm.subprocess.run") as run:
            _, lock = prepare_pi_npm(self.archive({"package-lock.json": self.lock}), "1.1.0", self.fetch_json)
        self.assertEqual(lock, self.lock)
        run.assert_not_called()

    def test_shrinkwrap_takes_precedence(self):
        other_lock = copy.deepcopy(self.lock)
        other_lock["version"] = "0.0.0"
        _, lock = prepare_pi_npm(self.archive({"npm-shrinkwrap.json": self.lock, "package-lock.json": other_lock}), "1.1.0", self.fetch_json)
        self.assertEqual(lock, self.lock)

    def test_missing_lock_is_generated_safely_in_tmp(self):
        def npm_run(command, *, cwd, check):
            self.assertTrue(check)
            self.assertEqual(command[:2], ["npm", "install"])
            for flag in ("--package-lock-only", "--lockfile-version=3", "--ignore-scripts", "--no-audit", "--no-fund", "--registry=https://registry.npmjs.org/", "--userconfig=/dev/null"):
                self.assertIn(flag, command)
            self.assertEqual(cwd.parent, pathlib.Path("/tmp"))
            self.assertEqual(pathlib.Path(command[command.index("--cache") + 1]).parent, cwd)
            manifest = json.loads((cwd / "package.json").read_text())
            self.assertNotIn("devDependencies", manifest)
            self.assertEqual(manifest["dependencies"], self.package["dependencies"])
            (cwd / "package-lock.json").write_text(json.dumps(self.lock))

        with patch("pi_npm.subprocess.run", side_effect=npm_run) as run:
            _, lock = prepare_pi_npm(self.archive({}), "1.1.0", self.fetch_json)
        self.assertEqual(lock, self.lock)
        run.assert_called_once()
        self.assertFalse(run.call_args.kwargs["cwd"].exists())

    def test_rejects_wrong_package_version_before_npm(self):
        with patch("pi_npm.subprocess.run") as run:
            with self.assertRaisesRegex(ValueError, "package name or version mismatch"):
                prepare_pi_npm(self.archive({}), "1.2.0", self.fetch_json)
        run.assert_not_called()

    def test_rejects_mismatched_lock_instead_of_regenerating(self):
        self.lock["version"] = "1.0.0"
        with patch("pi_npm.subprocess.run") as run:
            with self.assertRaisesRegex(ValueError, "lock name or version mismatch"):
                prepare_pi_npm(self.archive({"npm-shrinkwrap.json": self.lock}), "1.1.0", self.fetch_json)
        run.assert_not_called()

    def test_rejects_mismatched_lock_root(self):
        self.lock["packages"][""]["version"] = "1.0.0"
        with self.assertRaisesRegex(ValueError, "lock name or version mismatch"):
            prepare_pi_npm(self.archive({"npm-shrinkwrap.json": self.lock}), "1.1.0", self.fetch_json)

    def test_propagates_npm_failure(self):
        with patch("pi_npm.subprocess.run", side_effect=subprocess.CalledProcessError(1, ["npm"])):
            with self.assertRaises(subprocess.CalledProcessError):
                prepare_pi_npm(self.archive({}), "1.1.0", self.fetch_json)

    def test_missing_npm_has_actionable_error(self):
        with patch("pi_npm.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError, "requires npm"):
                prepare_pi_npm(self.archive({}), "1.1.0", self.fetch_json)

    def test_hydrates_only_missing_first_party_integrity(self):
        self.lock["packages"]["node_modules/@earendil-works/pi-ai"] = {
            "version": "1.1.0",
            "resolved": "https://registry.npmjs.org/@earendil-works/pi-ai/-/pi-ai-1.1.0.tgz",
        }
        self.fetch_json = Mock(return_value={"dist": {"integrity": "sha512-official"}})
        _, lock = prepare_pi_npm(self.archive({"npm-shrinkwrap.json": self.lock}), "1.1.0", self.fetch_json)
        self.assertEqual(lock["packages"]["node_modules/@earendil-works/pi-ai"]["integrity"], "sha512-official")
        self.assertEqual(lock["packages"]["node_modules/chalk"]["integrity"], "sha512-existing")
        self.fetch_json.assert_called_once_with("https://registry.npmjs.org/@earendil-works%2Fpi-ai/1.1.0")


if __name__ == "__main__":
    unittest.main()
