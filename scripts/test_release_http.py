import os
import unittest
import urllib.request
from unittest.mock import Mock, patch

from release_http import fetch, fetch_json


class ReleaseHttpTests(unittest.TestCase):
    def request(self, url, token="test-github-token"):
        response = Mock()
        response.read.return_value = b'{"version": "1.1.0"}'
        with patch.dict(os.environ, {"GH_TOKEN": token}), patch("release_http.urllib.request.urlopen") as open_url:
            open_url.return_value.__enter__.return_value = response
            self.assertEqual(fetch(url), response.read.return_value)
        open_url.assert_called_once()
        self.assertEqual(open_url.call_args.kwargs["timeout"], 120)
        return open_url.call_args.args[0]

    def test_authenticates_only_https_github_api(self):
        request = self.request("https://api.github.com/repos/openai/codex/releases/latest")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-github-token")
        self.assertNotIn("Authorization", request.headers)

    def test_does_not_send_github_token_to_upstream_providers(self):
        for url in (
            "https://persistent.oaistatic.com/codex-app-prod/linux/deb/dists/stable/main/binary-amd64/Packages",
            "https://registry.npmjs.org/@earendil-works/pi-coding-agent/latest",
            "https://downloads.claude.ai/claude-code-releases/2.1.296/manifest.json",
        ):
            with self.subTest(url=url):
                self.assertIsNone(self.request(url).get_header("Authorization"))

    def test_does_not_authenticate_http_or_lookalike_hosts(self):
        for url in ("http://api.github.com/", "https://api.github.com.example.com/", "https://api.github.com@other.example/"):
            with self.subTest(url=url):
                self.assertIsNone(self.request(url).get_header("Authorization"))

    def test_github_api_works_without_token(self):
        self.assertIsNone(self.request("https://api.github.com/repos/openai/codex/releases/latest", token="").get_header("Authorization"))

    def test_redirect_does_not_forward_token(self):
        request = self.request("https://api.github.com/repos/openai/codex/releases/latest")
        redirect = urllib.request.HTTPRedirectHandler().redirect_request(
            request, None, 302, "Found", {}, "https://other.example/releases/latest"
        )
        self.assertIsNone(redirect.get_header("Authorization"))

    def test_decodes_json(self):
        with patch("release_http.fetch", return_value=b'{"version": "1.1.0"}'):
            self.assertEqual(fetch_json("https://registry.npmjs.org/example/latest"), {"version": "1.1.0"})


if __name__ == "__main__":
    unittest.main()
