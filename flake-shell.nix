{
  perSystem = {
    lib,
    pkgsUnstable,
    ...
  }:
    with lib;
    with builtins; {
      devshells.default = {
        name = "nix-gpt";
        packages = with pkgsUnstable; [
          faiss
          httpie
          poetry
          poppler
          python311
          stdenv
          tesseract
        ];
        commands = let
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
          map poetryCommand commandList;
        env = [
          {
            name = "LD_LIBRARY_PATH";
            value = "${makeLibraryPath (with pkgsUnstable; [
              stdenv.cc.cc.lib
            ])}";
          }
        ];
      };
    };
}
