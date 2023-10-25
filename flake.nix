{
  description = "nix-gpt";

  nixConfig = {
    extra-substituters = ["https://nix-community.cachix.org"];
    extra-trusted-public-keys = ["nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="];
  };

  inputs = {
    # packages
    nixpkgs.url = "github:nixos/nixpkgs/23.05";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixpkgs-unstable";

    # flake-parts
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };
    flake-root.url = "github:srid/flake-root";
    systems.url = "github:nix-systems/default";
    process-compose-flake.url = "github:Platonic-Systems/process-compose-flake";
    services-flake.url = "github:juspay/services-flake";

    # utils
    devshell = {
      url = "github:numtide/devshell";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    flake-compat = {
      url = "github:nix-community/flake-compat";
      flake = false;
    };
    devour-flake = {
      url = "github:srid/devour-flake";
      flake = false;
    };
    haumea = {
      url = "github:nix-community/haumea/v0.2.2";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    lib-extras = {
      url = "github:aldoborrero/lib-extras";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs @ {
    flake-parts,
    haumea,
    nixpkgs,
    nixpkgs-unstable,
    ...
  }: let
    lib = nixpkgs-unstable.lib.extend (l: _: (inputs.lib-extras.lib l));
    localInputs = haumea.lib.load {
      src = ./.;
      loader = haumea.lib.loaders.path;
    };
  in
    flake-parts.lib.mkFlake {
      inherit inputs;
      specialArgs = {inherit lib localInputs;};
    }
    {
      imports = [
        inputs.flake-root.flakeModule
        inputs.treefmt-nix.flakeModule
        inputs.devshell.flakeModule
      ];
      systems = ["x86_64-linux"];
      perSystem = {
        pkgs,
        pkgsUnstable,
        system,
        config,
        ...
      }: {
        # nixpkgs
        _module.args = {
          pkgs = lib.nix.mkNixpkgs {
            inherit system;
            inherit (inputs) nixpkgs;
          };
          pkgsUnstable = lib.nix.mkNixpkgs {
            inherit system;
            nixpkgs = inputs.nixpkgs-unstable;
          };
        };

        # shell
        devshells.default = {
          name = "hacienda-gpt";
          packages = with pkgsUnstable; [
            faiss
            httpie
            playwright
            poetry
            poppler
            python311
            stdenv
            tesseract
          ];
          commands = with lib;
          with builtins; let
            poetryCommand = {
              bin,
              args ? ["$@"],
            }: {
              category = "python";
              name = "${bin}";
              help = "Run ${bin}";
              command = "poetry run ${bin} ${concatStringsSep " " args}";
            };
            commandList = [
              {bin = "pytest";}
              {bin = "streamlit";}
            ];
          in
            (map poetryCommand commandList)
            ++ [
              {
                category = "Tools";
                name = "fmt";
                help = "Format the source tree";
                command = "nix fmt";
              }
              {
                category = "Tools";
                name = "check";
                help = "Checks the source tree";
                command = "nix flake check";
              }
            ];
          env = with lib; [
            {
              name = "LD_LIBRARY_PATH";
              value = "${makeLibraryPath (with pkgsUnstable; [
                stdenv.cc.cc.lib
              ])}";
            }
            {
              name = "PLAYWRIGHT_BROWSERS_PATH";
              value = pkgsUnstable.playwright-driver.browsers-chromium;
            }
            {
              name = "PLAYWRIGHT_BROWSERS_BINARY_PATH";
              value = "${pkgsUnstable.playwright-driver.browsers-chromium}/chromium-1076/chrome-linux/chrome";
            }
            {
              name = "PLAYWRIGHT_NODEJS_PATH";
              value = getExe pkgsUnstable.nodejs_18;
            }
          ];
        };

        # checks
        checks = with lib;
        # merge in the package derivations to force a build of all packages during a `nix flake check`
          mapAttrs' (n: nameValuePair "package-${n}") self'.packages;

        # formatter
        treefmt.config = {
          inherit (config.flake-root) projectRootFile;
          flakeFormatter = true;
          flakeCheck = true;
          programs = {
            alejandra.enable = true;
            black.enable = true;
            deadnix.enable = true;
            mdformat.enable = true;
            prettier.enable = true;
            ruff.enable = true;
          };
          settings.formatter = {
            prettier.excludes = [
              "*.md"
              "./tests/*"
              "*.html"
            ];
            ruff.options = ["--fix"];
          };
        };
      };
    };
}
