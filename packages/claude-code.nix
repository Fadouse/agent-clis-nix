{
  lib,
  stdenvNoCC,
  fetchurl,
  installShellFiles,
  makeBinaryWrapper,
  autoPatchelfHook,
  alsa-lib,
  procps,
  ripgrep,
  bubblewrap,
  socat,
  versionCheckHook,
  writableTmpDirAsHomeHook,
}:

stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "claude-code";
  version = "2.1.261";

  src = fetchurl {
    url = "https://downloads.claude.ai/claude-code-releases/${finalAttrs.version}/linux-x64/claude";
    hash = "sha256-SuQN0XhOhXU+dC4J8mfSnsu4KJA2GtOBfSdWCGbTZKY=";
  };

  dontUnpack = true;
  dontBuild = true;
  dontStrip = true;

  nativeBuildInputs = [
    autoPatchelfHook
    installShellFiles
    makeBinaryWrapper
  ];

  installPhase = ''
    runHook preInstall
    install -Dm755 "$src" "$out/bin/claude"
    install -Dm444 ${./claude-code.LICENSE.md} "$out/share/licenses/claude-code/LICENSE.md"
    wrapProgram "$out/bin/claude" \
      --set DISABLE_AUTOUPDATER 1 \
      --set-default FORCE_AUTOUPDATE_PLUGINS 1 \
      --set DISABLE_INSTALLATION_CHECKS 1 \
      --set USE_BUILTIN_RIPGREP 0 \
      --prefix LD_LIBRARY_PATH : ${lib.makeLibraryPath [ alsa-lib ]} \
      --prefix PATH : ${
        lib.makeBinPath [
          procps
          ripgrep
          bubblewrap
          socat
        ]
      }
    runHook postInstall
  '';

  doInstallCheck = true;
  nativeInstallCheckInputs = [
    writableTmpDirAsHomeHook
    versionCheckHook
  ];
  versionCheckKeepEnvironment = [ "HOME" ];
  versionCheckProgramArg = "--version";

  meta = {
    description = "Anthropic Claude Code agentic coding tool";
    homepage = "https://github.com/anthropics/claude-code";
    downloadPage = "https://claude.com/product/claude-code";
    license = lib.licenses.unfree;
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
    platforms = [ "x86_64-linux" ];
    mainProgram = "claude";
  };
})
