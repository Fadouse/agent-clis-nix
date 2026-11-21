{
  lib,
  buildNpmPackage,
  fetchurl,
  nodejs_24,
  makeBinaryWrapper,
  ripgrep,
  fd,
  versionCheckHook,
  writableTmpDirAsHomeHook,
}:

buildNpmPackage (finalAttrs: {
  pname = "pi-coding-agent";
  version = "1.6.0";

  # Official npm releases carry the built JavaScript, including hydrated model
  # data that is unavailable when building the tag source offline.
  src = fetchurl {
    url = "https://registry.npmjs.org/@earendil-works/pi-coding-agent/-/pi-coding-agent-${finalAttrs.version}.tgz";
    hash = "sha256-hdXeQE4BnoUMkO6axtxsFiQNoSL9zgMUiVYIFkAwM2s=";
  };
  sourceRoot = "package";

  nodejs = nodejs_24;
  npmDepsHash = "sha256-RpyPYDKPH9P+rNBE5SDFzelyxFvamz8z7z6SRIa9m10=";
  npmRebuildFlags = [ "--ignore-scripts" ];
  dontNpmBuild = true;

  nativeBuildInputs = [ makeBinaryWrapper ];

  # The updater preserves upstream locks (filling missing first-party SRI) or
  # generates one from the official registry when the tarball omits its lock.
  postPatch = ''
    cp ${./pi-coding-agent.package.json} package.json
    cp ${./pi-coding-agent.npm-shrinkwrap.json} npm-shrinkwrap.json
  '';

  postInstall = ''
    install -Dm444 ${./pi-coding-agent.LICENSE} "$out/share/licenses/pi-coding-agent/LICENSE"
  '';

  postFixup = ''
    wrapProgram "$out/bin/pi" --prefix PATH : ${
      lib.makeBinPath [
        ripgrep
        fd
      ]
    }
  '';

  doInstallCheck = true;
  nativeInstallCheckInputs = [
    writableTmpDirAsHomeHook
    versionCheckHook
  ];
  versionCheckKeepEnvironment = [ "HOME" ];
  versionCheckProgram = "${placeholder "out"}/bin/pi";
  versionCheckProgramArg = "--version";

  meta = {
    description = "Coding agent CLI with read, bash, edit, write tools and session management";
    homepage = "https://pi.dev/";
    changelog = "https://github.com/earendil-works/pi/blob/v${finalAttrs.version}/packages/coding-agent/CHANGELOG.md";
    license = lib.licenses.mit;
    platforms = lib.platforms.unix;
    mainProgram = "pi";
  };
})
