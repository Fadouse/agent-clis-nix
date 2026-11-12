#!/usr/bin/env bash
set -euo pipefail

desktop="$1/share/applications/grok-bot.desktop"
chmod u+w "$1/share/applications" "$desktop"
desktop-file-edit --set-key=Exec --set-value="$1/bin/grok-bot -- %U" "$desktop"
desktop-file-validate "$desktop"
