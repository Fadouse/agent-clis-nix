{
  lib,
  stdenvNoCC,
  fetchurl,
  dpkg,
  buildFHSEnv,
  writeShellScript,
}:

let
  version = "26.908.40834";

  # Preserve OpenAI's upstream ELF layout and provide its Debian runtime in an
  # FHS environment, rather than patching the bundled Electron and Codex ELFs.
  payload = stdenvNoCC.mkDerivation {
    pname = "chatgpt-upstream";
    inherit version;

    src = fetchurl {
      url = "https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_${version}_amd64.deb";
      hash = "sha256-2je457zvquoBnEeMrL5sc+4d3RXg4euzx+8KQt2BisI=";
    };

    nativeBuildInputs = [ dpkg ];
    dontUnpack = true;
    dontConfigure = true;
    dontBuild = true;
    dontFixup = true;

    installPhase = ''
      runHook preInstall

      dpkg-deb --extract "$src" extracted
      mkdir -p "$out/lib" "$out/share"
      cp -a extracted/usr/lib/chatgpt "$out/lib/"
      cp -a extracted/usr/share/applications "$out/share/"
      cp -a extracted/usr/share/pixmaps "$out/share/"

      runHook postInstall
    '';
  };

  launcher = writeShellScript "chatgpt-fhs-launcher" ''
    unset LD_PRELOAD
    exec ${payload}/lib/chatgpt/ChatGPT \
      --enable-features=UseOzonePlatform \
      --ozone-platform=wayland \
      --enable-wayland-ime \
      "$@"
  '';
in
buildFHSEnv {
  pname = "chatgpt";
  inherit version;

  runScript = launcher;
  includeClosures = true;

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
      git
      glib
      gtk3
      libGL
      libgbm
      libdrm
      libnotify
      libpulseaudio
      libsecret
      libusb1
      libxkbcommon
      nspr
      nss
      openssl
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
      libxcb
      zlib
    ];

  extraInstallCommands = ''
    mkdir -p "$out/share/applications" "$out/share/pixmaps"
    cp ${payload}/share/applications/chatgpt.desktop \
      "$out/share/applications/chatgpt.desktop"
    cp ${payload}/share/pixmaps/chatgpt.png \
      "$out/share/pixmaps/chatgpt.png"
  '';

  meta = {
    description = "ChatGPT desktop app with ChatGPT, Work, and Codex";
    homepage = "https://developers.openai.com/codex/app";
    license = lib.licenses.unfree;
    platforms = [ "x86_64-linux" ];
    mainProgram = "chatgpt";
  };
}
