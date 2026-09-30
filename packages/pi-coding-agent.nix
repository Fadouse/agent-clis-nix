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
  version = "0.99.1";

  # Official npm release built by the upstream tag v0.84.1. The tag source
  # omits hydrated model data required by its offline build, while this release
  # carries the already-built JavaScript and its upstream npm-shrinkwrap.json.
  src = fetchurl {
    url = "https://registry.npmjs.org/@earendil-works/pi-coding-agent/-/pi-coding-agent-${finalAttrs.version}.tgz";
    hash = "sha256-ZoZZKtrqGQkshclPXUAyPb89sUHpDrPt6enocwKr3R0=";
  };
  sourceRoot = "package";

  nodejs = nodejs_24;
  npmDepsHash = "sha256-W3nbpczNYv2wjMWp3IZCOqZ5Uv4i4KOhi50lQ6WHFF4=";
  npmRebuildFlags = [ "--ignore-scripts" ];
  dontNpmBuild = true;

  nativeBuildInputs = [ makeBinaryWrapper ];

  # Upstream 0.84.1 omitted SRI fields for its six first-party tarballs.
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
