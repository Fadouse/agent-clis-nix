{
  lib,
  stdenvNoCC,
  fetchurl,
  versionCheckHook,
}:

stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "codex";
  version = "0.153.4";

  src = fetchurl {
    url = "https://github.com/openai/codex/releases/download/rust-v${finalAttrs.version}/codex-package-x86_64-unknown-linux-musl.tar.gz";
    hash = "sha256-qCIYfhokIMYcWSZyG/vYeHAe2VVHybsNTeRJiha6GCE=";
  };

  sourceRoot = ".";
  dontBuild = true;
  dontStrip = true;

  installPhase = ''
    runHook preInstall
    mkdir -p "$out/libexec/codex" "$out/bin" "$out/share/licenses/codex"
    cp -a . "$out/libexec/codex/"
    ln -s ../libexec/codex/bin/codex "$out/bin/codex"
    install -Dm444 ${./codex.LICENSE} "$out/share/licenses/codex/LICENSE"
    runHook postInstall
  '';

  doInstallCheck = true;
  nativeInstallCheckInputs = [ versionCheckHook ];
  versionCheckProgramArg = "--version";

  meta = {
    description = "OpenAI Codex coding agent";
    homepage = "https://github.com/openai/codex";
    changelog = "https://github.com/openai/codex/releases/tag/rust-v${finalAttrs.version}";
    license = lib.licenses.asl20;
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
    platforms = [ "x86_64-linux" ];
    mainProgram = "codex";
  };
})
