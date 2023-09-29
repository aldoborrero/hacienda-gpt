lib: let
  # Filesystem related functions
  fs = rec {
    /*
    Function: flattenSet
    Synopsis: Flattens a nested attribute set (tree) into a single-level attribute set.

    Parameters:
      - tree (attrset): A nested attribute set

    Returns:
      - An attribute set where keys are constructed in reverse DNS notation, based on the nesting.

    Example:
      Input: { a = { b = { c = <path>; }; }; }
      Output: { "a.b.c" = <path>; }

    Description:
      The function traverses the nested attribute set and produces a flattened attribute set.
      It uses dot-based reverse DNS notation to concatenate the nested keys.
    */
    flattenSet = tree: let
      folder = sum: path: val: let
        pathStr = builtins.concatStringsSep "." path;
      in
        if builtins.isAttrs val
        then (recurse sum path val)
        else if builtins.isPath val
        then sum // {"${pathStr}" = val;}
        else sum;
      recurse = sum: path: val:
        builtins.foldl' (s: k: folder s (path ++ [k]) val.${k}) sum (builtins.attrNames val);
    in
      recurse {} [] tree;

    /*
    Function: collectNixFiles
    Synopsis: Recursively collects `.nix` files from a directory into an attribute set.

    Parameters:
      - dirPath (string): The directory path to collect `.nix` files from.

    Returns:
      - An attribute set mapping filenames (without the `.nix` suffix) to their paths.
    */
    collectNixFiles = dirPath: let
      isNixOrDir = file: type: (type == "regular" && lib.hasSuffix ".nix" file) || (type == "directory");
      collect = file: type: {
        name = lib.removeSuffix ".nix" file;
        value = let
          path = dirPath + "/${file}";
        in
          if (type == "regular") || (type == "directory" && builtins.pathExists (path + "/default.nix"))
          then path
          else collectNixFiles path;
      };
      files = lib.filterAttrs isNixOrDir (builtins.readDir dirPath);
    in
      lib.filterAttrs (_: v: v != {}) (lib.mapAttrs' collect files);

    /*
    Function: collectFiles
    Synopsis: Recursively collects files with specified extensions from a directory into an attribute set.

    Parameters:
      - exts (list of strings): A list of file extensions to collect (e.g., [".nix", ".json"]).
      - dirPath (string): The directory path to collect files from.

    Returns:
      - An attribute set mapping filenames (without their extensions) to their paths.

    Description:
      The function traverses the directory and its subdirectories to locate files with extensions specified in the `exts` parameter. It then returns an attribute set mapping the base filenames to their respective paths. Directories are also recursively traversed to find valid files.

    Example Usage:
      collectFiles [".nix", ".json"] /some/directory
    */
    collectFiles = exts: dirPath: let
      isValidFile = file: type:
        (type == "regular" && lib.any (suffix: lib.hasSuffix suffix file) exts) || (type == "directory");
      removeAnySuffix = suffixes: str:
        lib.foldl (acc: suffix: lib.removeSuffix suffix acc) str suffixes;
      collect = file: type: {
        name = removeAnySuffix exts file;
        value = let
          path = dirPath + "/${file}";
        in
          if type == "regular"
          then path
          else collectFiles exts path;
      };
      files = lib.filterAttrs isValidFile (builtins.readDir dirPath);
    in
      lib.filterAttrs (_: v: v != {}) (lib.mapAttrs' collect files);

    mergeAny = lhs: rhs:
      lhs
      // builtins.mapAttrs (name: value:
        if builtins.isAttrs value
        then lhs.${name} or {} // value
        else if builtins.isList value
        then lhs.${name} or [] ++ value
        else value)
      rhs;
  };

  # Nix related functions
  nix = {
    /*
    Function: mkNixpkgs
    Synopsis: Creates a custom Nixpkgs configuration.

    Parameters:
      - system (string): Target system, e.g., "x86_64-linux".
      - inputs (attrset, optional): Custom inputs for the Nixpkgs configuration.
      - overlays (list, optional): List of overlays to apply.
      - nixpkgs (path, optional): Path to the Nixpkgs repository. Defaults to inputs.nixpkgs.
      - config (attrset, optional): Additional Nixpkgs configuration settings.

    Returns:
      - A configured Nixpkgs environment suitable for importing.

    Example:
      mkNixpkgs {
        system = "x86_64-linux";
        overlays = [ myOverlay ];
      }

    Description:
      The function imports a Nixpkgs environment with the specified target system, custom inputs,
      and overlays. It also accepts additional Nixpkgs configuration settings.
    */
    mkNixpkgs = {
      system,
      nixpkgs,
      overlays ? [],
      config ? {allowUnfree = true;},
    }:
      import nixpkgs {inherit system config overlays;};
  };
in {
  inherit fs nix;
}
