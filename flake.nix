{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/release-25.05";

  outputs =
    { nixpkgs, ... }:
    let
      systems = nixpkgs.lib.systems.flakeExposed;
    in
    {
      devShells = nixpkgs.lib.genAttrs systems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              (python3.withPackages (
                ps: with ps; [
                  pip
                ]
              ))
            ];

            venvDir = "./.venv";
            nativeBuildInputs = [ pkgs.python3Packages.venvShellHook ];
            postShellHook = ''
              pip install flask
              pip install flask-cors
              pip install python-dotenv
              pip install requests
              pip install backboard-sdk
            '';
          };
        }
      );
    };
}
