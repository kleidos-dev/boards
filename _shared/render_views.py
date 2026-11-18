# SPDX-License-Identifier: MIT
"""Orthographic silhouettes of a mesh, as shapely geometry.

``check_board_model.py`` compares a board model's front, left and top
silhouettes with the board's drawings through ``silhouette_polygon``. The
views are named as a person looking at the board sees them.
"""
from __future__ import annotations

import numpy as np
import shapely
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

#: Views of a mesh in a CAD frame (mm, +Z up): view -> (plot_x_dim,
#: plot_x_sign, plot_y_dim, plot_y_sign), with dims 0 = X, 1 = Y, 2 = Z.
_VIEW_AXES = {
    "front":  (0, +1, 2, +1),   # look along -Y
    "back":   (0, -1, 2, +1),   # look along +Y
    "top":    (0, +1, 1, +1),   # look along -Z
    "bottom": (0, +1, 1, -1),   # look along +Z
    "left":   (1, +1, 2, +1),   # look along +X
    "right":  (1, -1, 2, +1),   # look along -X
}


#: The same views of a board model in its glTF frame (+Y up the screen, +Z out of
#: the screen, +X to the device's right), drawn as a person looking at it sees
#: them: the front from +Z, the left side from -X (the front face to the right),
#: the top from +Y (the front face down).
MODEL_VIEW_AXES = {
    "front": (0, +1, 1, +1),
    "left":  (2, +1, 1, +1),
    "top":   (0, +1, 2, -1),
    "back":  (0, -1, 1, +1),
}


def silhouette_polygon(mesh: trimesh.Trimesh, view: str, axes: dict | None = None):
    """Return a shapely (Multi)Polygon = union of all triangle projections.

    *axes* maps a view name to (plot_x_dim, plot_x_sign, plot_y_dim,
    plot_y_sign); the default is the CAD frame (``_VIEW_AXES``).
    """
    px, sx, py, sy = (axes or _VIEW_AXES)[view]
    tri = mesh.triangles  # (N,3,3)
    if len(tri) == 0:
        return None
    pts2d = np.stack([sx * tri[:, :, px], sy * tri[:, :, py]], axis=-1)  # (N,3,2)
    polys = []
    for face in pts2d:
        try:
            p = Polygon(face)
            if p.is_valid and p.area > 0:
                polys.append(p)
            elif not p.is_valid:
                p = p.buffer(0)
                if not p.is_empty and p.area > 0:
                    polys.append(p)
        except Exception:
            continue
    if not polys:
        return None
    try:
        return unary_union(polys)
    except shapely.errors.GEOSException:
        # thousands of slivers can leave GEOS a ring it cannot close
        # ("TopologyException: Ring edge missing"); snapping every vertex to a
        # 1 um grid first gives it one it can
        return shapely.union_all(polys, grid_size=0.001)
