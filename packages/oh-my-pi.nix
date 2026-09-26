{
  lib,
  stdenvNoCC,
  fetchurl,
  makeBinaryWrapper,
  patchelf,
  glibc,
  git,
  gh,
  xdg-utils,
  pcre2,
}:

stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "oh-my-pi";
  version = "18.3.2";

  src = fetchurl {
    url = "https://github.com/can1357/oh-my-pi/releases/download/v${finalAttrs.version}/omp-linux-x64";
    hash = "sha256-jLvNS+p6e4YRahM1LzHjd4/U2T35MQNrsXcXOLBwJTQ=";
  };
  licenseFile = fetchurl {
    url = "https://github.com/can1357/oh-my-pi/releases/download/v${finalAttrs.version}/LICENSE";
    hash = "sha256-FsRfnWZ0QngfA/oZiRTMOavKpI7F7Y9kRkPlVMovv2M=";
  };
  thirdPartyNotices = fetchurl {
    url = "https://github.com/can1357/oh-my-pi/releases/download/v${finalAttrs.version}/THIRD-PARTY-NOTICES.txt";
    hash = "sha256-0MLnwFu011UESxP6VgvljQGrfJgLh4kkAKl5OX5Wmos=";
  };

  dontUnpack = true;
  dontBuild = true;
  dontConfigure = true;
  dontStrip = true;
  dontPatchELF = true;
  nativeBuildInputs = [
    makeBinaryWrapper
    patchelf
  ];

  installPhase = ''
    runHook preInstall
    install -Dm755 "$src" "$out/libexec/omp"
    install -Dm444 "$licenseFile" "$out/share/licenses/oh-my-pi/LICENSE"
    install -Dm444 "$thirdPartyNotices" "$out/share/licenses/oh-my-pi/THIRD-PARTY-NOTICES.txt"
    makeWrapper "$out/libexec/omp" "$out/bin/omp" \
      --suffix PATH : ${
        lib.makeBinPath [
          git
          gh
          xdg-utils
        ]
      } \
      --suffix LD_LIBRARY_PATH : ${lib.makeLibraryPath [ pcre2 ]}
    runHook postInstall
  '';

  postFixup = ''
    patchelf --set-interpreter ${glibc}/lib/ld-linux-x86-64.so.2 "$out/libexec/omp"
  '';

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck
    HOME=$(mktemp -d) "$out/bin/omp" --version 2>&1 | grep -F "omp/${finalAttrs.version}"
    runHook postInstallCheck
  '';

  meta = {
    description = "Oh My Pi coding agent";
    homepage = "https://github.com/can1357/oh-my-pi";
    changelog = "https://github.com/can1357/oh-my-pi/releases/tag/v${finalAttrs.version}";
    license = lib.licenses.mit;
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
    platforms = [ "x86_64-linux" ];
    mainProgram = "omp";
  };
})
