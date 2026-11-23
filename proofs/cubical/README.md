# Semplex Cubical Agda track

## Toolchain

- Agda: 2.9.0, local Windows x64 prebuilt binary at %LOCALAPPDATA%/Semplex/Agda/2.9.0/agda.exe.
- SHA-256 of the downloaded official release archive: 092438d549fb5e903ed35d94c81f2355fa469f5a994b1e3a2fa655d3b7593f0d.
- Official release: https://github.com/agda/agda/releases/tag/v2.9.0
- Cubical mode: --cubical=full.
- GHC/Cabal are not required for this prebuilt binary's typechecking workflow. No global PATH changes were made.

## Current verified modules

- src/Semplex/Cubical/Primitives.agda: minimal path primitives and path concatenation defined over Agda's cubical interval/path builtins.
- src/Semplex/Cubical/S1.agda: the circle HIT with a base point and a nontrivial loop constructor.
- src/Semplex/Cubical/S1Recursor.agda: nondependent and dependent circle eliminators with explicit base/loop computation equalities.
- src/Semplex/Cubical/BGroup2Skeleton.agda: a 2-dimensional HIT presentation skeleton for a group, with point, loops, and 2-cells for unit, multiplication, and inverse relations.

All four modules typecheck with Agda 2.9.0 in full cubical mode.

## Important mathematical boundary

BGroup2Skeleton is **not yet a complete classifying space BG**. Its 2-cells present the group relations, but the higher coherence cells (especially associativity coherence) and a proof/constructor establishing the intended 1-truncation are not yet present. Do not infer that its higher homotopy groups vanish or that it is already equivalent to the nerve/classifying space of the group.

The next HIT work is:
1. prove associativity coherence for path composition in the minimal primitive layer;
2. add the 3-dimensional coherence cell for group multiplication associativity;
3. add unit/inverse coherence and verify all coherence diagrams;
4. establish the 1-truncation needed for a genuine BG 1-type;
5. connect the loop space at base to the original group;
6. compare this HIT with the Lean action groupoid and its stabilizers.

A naive nondependent recursor for BGroup2Skeleton was attempted and removed after Agda exposed primTransp boundary mismatches. This is a genuine higher-elimination/coherence problem, not a passing theorem; see the research note.

## Compatibility findings

The official Cubical Agda library v0.9 archive was downloaded and its SHA-256 verified (a63aa690aacb90d40dadc215a08ab7b442f6aca1aae079a39c2801993d465d57). Its Prelude currently fails to import under Agda 2.9.0 because its Glue/Equiv import chain conflicts with the new builtin Sigma cubical mode. The v0.9 library metadata targets the older --cubical mode. The tested v0.9 archive was removed from the repository after the compatibility failure; the active project has no dependency on it.

Agda 2.8.0.2's official Windows binary launched but crashed with an internal Signature.hs error even on an empty module. The Agda 2.8.0 Windows binary exited with missing-runtime status -1073741515. Those failed local toolchain copies were removed. Agda 2.9.0 successfully typechecks the minimal custom HIT layer above. No GHC/Cabal toolchain was installed.

## Reproducible verification

Run from PowerShell:

    .\verify.ps1
