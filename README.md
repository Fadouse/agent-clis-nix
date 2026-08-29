# Fadouse Agent CLI Nix Packages

Self-maintained Nix derivations built from official upstream releases only.
No NUR, unstable nixpkgs input, third-party package recipe, or third-party binary cache is used.

Pinned packages:

- Anthropic Claude Code 2.1.220: official `downloads.claude.ai` native binary and manifest checksum.
- OpenAI Codex 0.150.1: official GitHub release asset.
- Pi Coding Agent 0.84.1: official npm release with audited registry integrity data.
- Riemann Agent: signed commit from `Fadouse/riemann-agent`, built from source.

The sole nixpkgs input is official `NixOS/nixpkgs/nixos-26.05`. The host input follows its own pinned nixpkgs. CI builds checks but publishes no binaries; deployment always builds locally.
