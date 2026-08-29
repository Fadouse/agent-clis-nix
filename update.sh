#!/usr/bin/env bash
set -euo pipefail
cat <<'EOF'
Update one package at a time:
1. Read the official upstream release notes and licenses.
2. Verify the official manifest/tag/asset or npm provenance.
3. Change the pinned version and use lib.fakeHash for changed source/dependency hashes.
4. Run nix flake check and isolated-HOME smoke tests locally.
5. Review and GPG-sign the commit and tag; do not publish CI binaries.
EOF
