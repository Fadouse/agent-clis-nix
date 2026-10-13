# Fadouse Agent CLI Nix Packages

Self-maintained Nix derivations built from official upstream releases only.
No NUR, unstable nixpkgs input, third-party package recipe, or third-party binary cache is used.

Current packages:

- Anthropic Claude Code 2.1.251: official `downloads.claude.ai` native binary and manifest checksum.
- OpenAI Codex 0.151.0: official GitHub release asset and digest.
- Grok Bot: automatically tracks the latest official stable release and Debian package from Cursor.
- Pi Coding Agent 0.84.4: official npm release with audited official registry integrity data.
- Oh My Pi 18.0.11: official `can1357/oh-my-pi` GitHub release assets and digests.
- Riemann Agent: signed commit from `Fadouse/riemann-agent`, built from source.

The sole nixpkgs input is official `NixOS/nixpkgs/nixos-26.05`. The host input follows its own pinned nixpkgs. CI builds checks but publishes no binaries; deployment always builds locally.

`grok-bot` includes the desktop launcher, icons, and `grokbot://` / `sand://` URL handlers. It selects native Wayland with input method support in a Wayland session and X11 otherwise. The official Debian payload and bundled Electron runtime are preserved in an FHS environment.

`update-agent-releases` runs daily and can be manually dispatched. It checks official OpenAI/Anthropic/Cursor/npm/GitHub release metadata, verifies and pins upstream digests (or computes SHA-256 from the official Grok Bot Debian download, whose feed has no digest), updates the Riemann input, fully builds all packages, and only then commits the synchronized package set to `main`. A later host `nix flake update` therefore updates NixOS and all managed agents together.
