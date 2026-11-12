import copy
import pathlib
import unittest

from omp_release import update_omp_nix


class OmpReleaseTests(unittest.TestCase):
    def setUp(self):
        self.text = (pathlib.Path(__file__).resolve().parents[1] / "packages/oh-my-pi.nix").read_text()
        self.release = {
            "tag_name": "v18.19.0",
            "draft": False,
            "prerelease": False,
            "assets": [
                {"name": "omp-linux-x64", "digest": "sha256:" + "11" * 32},
                {"name": "LICENSE", "digest": "sha256:" + "22" * 32},
            ],
        }

    def with_notices(self):
        release = copy.deepcopy(self.release)
        release["assets"].append({"name": "THIRD-PARTY-NOTICES.txt", "digest": "sha256:" + "33" * 32})
        return release

    def test_release_without_notices_removes_download_dependency(self):
        old = update_omp_nix(self.text, self.with_notices())
        updated = update_omp_nix(old, self.release)
        self.assertIn('  version = "18.19.0";', updated)
        self.assertIn("  thirdPartyNotices = null;", updated)
        self.assertNotIn('/THIRD-PARTY-NOTICES.txt";', updated)
        self.assertIn('hash = "sha256-ERERERERERERERERERERERERERERERERERERERERERE=";', updated)
        self.assertIn('hash = "sha256-IiIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiI=";', updated)

    def test_release_with_notices_restores_pinned_download(self):
        without = update_omp_nix(self.text, self.release)
        updated = update_omp_nix(without, self.with_notices())
        self.assertIn("  thirdPartyNotices = fetchurl {", updated)
        self.assertIn('/v${finalAttrs.version}/THIRD-PARTY-NOTICES.txt";', updated)
        self.assertIn('hash = "sha256-MzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzM=";', updated)

    def test_repeated_updates_are_idempotent(self):
        for release in (self.release, self.with_notices()):
            with self.subTest(notices=len(release["assets"]) == 3):
                updated = update_omp_nix(self.text, release)
                self.assertEqual(update_omp_nix(updated, release), updated)

    def test_missing_binary_or_license_is_an_error(self):
        for name in ("omp-linux-x64", "LICENSE"):
            with self.subTest(asset=name):
                release = copy.deepcopy(self.release)
                release["assets"] = [asset for asset in release["assets"] if asset["name"] != name]
                with self.assertRaisesRegex(ValueError, f"missing required asset: {name}"):
                    update_omp_nix(self.text, release)

    def test_present_assets_must_have_valid_sha256_digests(self):
        for index in range(3):
            for digest in (None, "sha512:" + "11" * 64, "sha256:abcd", "sha256:" + "zz" * 32):
                with self.subTest(asset=index, digest=digest):
                    release = self.with_notices()
                    release["assets"][index]["digest"] = digest
                    with self.assertRaisesRegex(ValueError, "no valid SHA-256 digest"):
                        update_omp_nix(self.text, release)

    def test_rejects_unstable_releases(self):
        for flag in ("draft", "prerelease"):
            with self.subTest(flag=flag):
                release = copy.deepcopy(self.release)
                release[flag] = True
                with self.assertRaisesRegex(ValueError, "not stable"):
                    update_omp_nix(self.text, release)
        self.release["tag_name"] = "v18.19.0-rc.1"
        with self.assertRaisesRegex(ValueError, "unexpected Oh My Pi release tag"):
            update_omp_nix(self.text, self.release)

    def test_missing_nix_attribute_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "cannot update Oh My Pi thirdPartyNotices"):
            update_omp_nix(self.text.replace("thirdPartyNotices =", "removedNotices ="), self.release)


if __name__ == "__main__":
    unittest.main()
