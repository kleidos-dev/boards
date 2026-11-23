<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# Pinned fonts

Inter sets the printed legends of the nine board models, in its Regular, Medium and Bold. `_shared/legend_mesh.py` reads the digests below from this file, refuses a TTF that does not match its pin, and triangulates the glyph outlines into a model's `*_legends_*` meshes. The files are the upstream release, unmodified, redistributed with their license (`inter/OFL.txt`).

## Inter (sans)

- Upstream: <https://github.com/rsms/inter>
- Release: `v4.1`
- License: SIL Open Font License 1.1 (`inter/OFL.txt`), "Copyright (c) 2016 The Inter Project Authors". Inter declares no Reserved Font Name.
- Files + SHA-256:
  - `inter/Inter-Regular.ttf` `40d692fce188e4471e2b3cba937be967878f631ad3ebbbdcd587687c7ebe0c82`
  - `inter/Inter-Medium.ttf` `97ad806f526e41546d46365bb3a393145f75b7b1568913db74549ad8b8dba872`
  - `inter/Inter-Bold.ttf` `288316099b1e0a47a4716d159098005eef7c0066921f34e3200393dbdb01947f`
