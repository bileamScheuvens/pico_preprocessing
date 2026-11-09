{
  description = "Devenv.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };
  outputs =
    {
      self,
      nixpkgs,
    }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        system = system;
        config.allowUnfree = true;
        # config.allowBroken = true;
        # config.cudaSupport = true;
      };
      python = pkgs.python312.override {
        packageOverrides = new: old: {
          lz4 = old.lz4.overridePythonAttrs (oldAttrs: {
            doCheck = false;
          });
          pybreaker = old.pybreaker.overridePythonAttrs (oldAttrs: {
            doCheck = false;
          });
          portalocker = old.portalocker.overridePythonAttrs (oldAttrs: {
            doCheck = false;
          });
          backrefs = old.backrefs.overridePythonAttrs (oldAttrs: {
            doCheck = false;
          });
        };
      };
    in
    {
      devShells.${system}.default = pkgs.mkShell rec {
        buildInputs = with pkgs; [
          (python.withPackages (
            ps: with ps; [
              # faiss
              openai
              tenacity
              # ipdb
              # joblib
              # matplotlib
              # nltk
              polars
              datasets
              omegaconf
              pyarrow
              pip
              pip-tools
              # plotly
              pudb
              # pytest
              # wandb

              (buildPythonPackage (finalAttrs: {
                pname = "lucene";
                version = "10.0.0";
                format = "wheel";
                __structuredAttrs = true;

                src = fetchurl {
                  url = "https://github.com/hscells/pylucene-packaged/raw/8e6222c/dist/lucene-${finalAttrs.version}-cp312-cp312-linux_x86_64.whl";
                  hash = "sha256-8tpdCJU7r4sSb+V6wb0pfgSM17i3E0tjO1ojbhGOBDg=";
                };

                nativeBuildInputs = [ autoPatchelfHook ];
                doCheck = false;

                buildInputs = [
                  stdenv.cc.cc.lib
                  jdk21_headless
                ];

                # libjvm.so isn't in $JDK/lib
                preFixup = ''
                  addAutoPatchelfSearchPath ${jdk21_headless}/lib/openjdk/lib/server
                '';

                pythonImportsCheck = [ "lucene" ];

              }))
            ]
          ))
        ];

        # shellHook = ''
        #   unset SOURCE_DATE_EPOCH
        #   export CUDA_PATH=${pkgs.cudatoolkit}
        #   export LD_LIBRARY_PATH=${
        #     pkgs.lib.makeLibraryPath (
        #       [
        #         "/run/opengl-driver" # Needed to find libGL.so
        #       ]
        #       ++ buildInputs
        #     )
        #   }:$LD_LIBRARY_PATH
        #
        #   # Set LIBRARY_PATH to help the linker find the CUDA static libraries
        #   export LIBRARY_PATH=${
        #     pkgs.lib.makeLibraryPath [
        #       pkgs.cudatoolkit
        #     ]
        #   }:$LIBRARY_PATH
        #   export LD_PRELOAD=${pkgs.cudaPackages.cuda_nvrtc.lib}/lib/libnvrtc.so.12:$LD_PRELOAD
        # '';
      };
    };
}
