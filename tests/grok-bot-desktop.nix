{ runCommand, desktop-file-utils }:

runCommand "grok-bot-desktop-test" { nativeBuildInputs = [ desktop-file-utils ]; } ''
  root="$TMPDIR/grok-bot"
  mkdir -p "$root/share/applications"
  desktop="$root/share/applications/grok-bot.desktop"

  for upstreamExec in 'grok-bot %U' 'grok-bot -- %U'; do
    cat > "$desktop" <<EOF
  [Desktop Entry]
  Name=Grok Bot
  Exec=$upstreamExec
  Terminal=false
  Type=Application
  Icon=grok-bot
  MimeType=x-scheme-handler/grokbot;x-scheme-handler/sand;
  Categories=Development;
  EOF

    # cp -a from a Nix store payload preserves read-only directory and file modes.
    chmod a-w "$root/share/applications" "$desktop"
    bash ${../scripts/fix-grok-desktop.sh} "$root"
    grep -Fx "Exec=$root/bin/grok-bot -- %U" "$desktop"
    grep -Fx 'Name=Grok Bot' "$desktop"
    grep -Fx 'Icon=grok-bot' "$desktop"
    grep -Fx 'MimeType=x-scheme-handler/grokbot;x-scheme-handler/sand;' "$desktop"
  done

  touch "$out"
''
