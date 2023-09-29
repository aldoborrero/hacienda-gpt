{
  perSystem = {
    self',
    lib,
    ...
  }:
    with lib; {
      checks =
        # merge in the package derivations to force a build of all packages during a `nix flake check`
        mapAttrs' (n: nameValuePair "package-${n}") self'.packages;

      devshells.default.commands = [
        {
          category = "Tools";
          name = "check";
          help = "Checks the source tree";
          command = "nix flake check";
        }
      ];
    };
}
