{
  description = "Fadouse-maintained packages from official upstream agent releases";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    riemann-agent = {
      url = "github:Fadouse/riemann-agent";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      riemann-agent,
    }:
    let
      systems = [ "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      pkgsFor =
        system:
        import nixpkgs {
          inherit system;
          config.allowUnfreePredicate = pkg: nixpkgs.lib.getName pkg == "claude-code";
        };
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
        in
        rec {
          claude-code = pkgs.callPackage ./packages/claude-code.nix { };
          codex = pkgs.callPackage ./packages/codex.nix { };
          pi-coding-agent = pkgs.callPackage ./packages/pi-coding-agent.nix { };
          oh-my-pi = pkgs.callPackage ./packages/oh-my-pi.nix { };
          riemann-agent = inputs.riemann-agent.packages.${system}.riemann-agent;
          default = riemann-agent;
        }
      );

      checks = forAllSystems (system: self.packages.${system});
      formatter = forAllSystems (system: (pkgsFor system).nixfmt);
    };
}
