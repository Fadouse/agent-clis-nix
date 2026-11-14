{
  lib,
  stdenvNoCC,
  fetchurl,
  dpkg,
  buildFHSEnv,
  writeShellScript,
  desktop-file-utils,
}:

let
  version = "1.1.0";
  revision = "83d46d618ef4c12afa17edd8e3c29d6caf046d17";

  # Keep the official Electron runtime and native modules together, unpatched.
  payload = stdenvNoCC.mkDerivation {
    pname = "grok-bot-upstream";
    inherit version;

    src = fetchurl {
      url = "https://downloads.cursor.com/grokbot/stable/${revision}/linux/x64/grok-bot_${version}_amd64.deb";
      hash = "sha256-WwL7IVED7e2U7J84GnkNcfZyfwF2gcft0bVvK4z6Vy0=";
    };

    nativeBuildInputs = [ dpkg ];
    dontUnpack = true;
    dontConfigure = true;
    dontBuild = true;
    dontFixup = true;

    installPhase = ''
      runHook preInstall

      dpkg-deb --extract "$src" extracted
      mkdir -p "$out/opt" "$out/share"
      cp -a "extracted/opt/Grok Bot" "$out/opt/"
      cp -a extracted/usr/share/. "$out/share/"

      runHook postInstall
    '';
  };

  launcher = writeShellScript "grok-bot-fhs-launcher" ''
    unset LD_PRELOAD
    flags=(--ozone-platform=x11)
    if [[ -n "''${WAYLAND_DISPLAY:-}" || "''${XDG_SESSION_TYPE:-}" == wayland ]]; then
      flags=(--ozone-platform=wayland --enable-wayland-ime)
    fi
    exec "${payload}/opt/Grok Bot/grok-bot" "''${flags[@]}" "$@"
  '';
in
buildFHSEnv {
  pname = "grok-bot";
  inherit version;

  runScript = launcher;
  includeClosures = true;
  nativeBuildInputs = [ desktop-file-utils ];

  targetPkgs =
    pkgs: with pkgs; [
      alsa-lib
      at-spi2-atk
      at-spi2-core
      atk
      cairo
      coreutils
      cups
      dbus
      expat
      fontconfig
      freetype
      gcc.cc.lib
      glib
      gtk3
      libGL
      libgbm
      libdrm
      libnotify
      libpulseaudio
      libsecret
      libuuid
      libxkbcommon
      nspr
      nss
      pango
      systemd
      wayland
      xdg-utils
      libx11
      libxcomposite
      libxdamage
      libxext
      libxfixes
      libxrandr
      libxscrnsaver
      libxtst
      libxcb
      zlib
    ];

  extraInstallCommands = ''
    mkdir -p "$out/share"
    cp -a ${payload}/share/. "$out/share/"
    bash ${../scripts/fix-grok-desktop.sh} "$out"
  '';

  meta = {
    description = "Grok Bot desktop agent";
    homepage = "https://x.ai/bot";
    downloadPage = "https://cursor.com/download/bot";
    license = lib.licenses.unfree;
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
    platforms = [ "x86_64-linux" ];
    mainProgram = "grok-bot";
  };
}
