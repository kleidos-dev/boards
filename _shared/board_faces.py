# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""The six faces of a board, and how a drawing of one lies on the model

A board prints on more than its front: a sticker on the back, a rating label
on the top edge, a name on a side. Each face's prints are drawn once, in a
drawing of that face (``svg/front.svg``, ``svg/back.svg``, ...), seen straight
on by someone looking at it, and built into the model as flat sheets
(``legend_mesh.py``). This module says, for each face, how that drawing's
frame lies in the model's build frame (+X to the device's right as its front
is seen, +Y up the screen, +Z out of the screen).

**A drawing's frame.** 1 mm a unit, ``u`` across to the right and ``v`` down,
as the face's viewer sees it, from the corner of the face that viewer sees at
the top left:

=========  =====================================  ==========  ============  =====================
face       how its viewer holds the board          ``u`` runs  up runs       the origin, keys
=========  =====================================  ==========  ============  =====================
front      screen towards them, the top up         +X          +Y            ``left_x``, ``top_y``
back       turned about its long axis, top up      -X          +Y            ``right_x``, ``top_y``
top        its top edge tilted towards them        +X          -Z            ``left_x``, ``back_z``
bottom     its bottom edge tilted towards them     +X          +Z            ``left_x``, ``front_z``
left       turned to show its left side, top up    +Z          +Y            ``back_z``, ``top_y``
right      turned to show its right side, top up   -Z          +Y            ``front_z``, ``top_y``
=========  =====================================  ==========  ============  =====================

So a back drawing's ``u`` is measured from the case's right edge as its front
is seen (the left edge as its back is seen), a top drawing has the front at
its bottom, and a side drawing has the front on the right of the left side's
and on the left of the right side's. The front is the frame of
``measurements.json`` (x across from the case's left edge, y down from its
top edge), which every other face derives from.

Each face's basis is right-handed: ``u`` times up is the face's outward
normal. Positions measured along ``u`` and up (``a`` and ``b``) are therefore a
plane in which counterclockwise is counterclockwise as the face's viewer sees
it: a sheet triangulated counterclockwise in (a, b) and laid on the face faces
its viewer, and needs no winding of its own.

Needs numpy only.
"""

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

#: Each face's ``u`` axis and up axis, as (axis index, sign), and the two keys
#: that place its drawing's origin: the build-frame coordinate of ``u`` = 0 on
#: the ``u`` axis, then of ``v`` = 0 on the up axis.
FACES = {
    "front": ((0, 1), (1, 1), ("left_x", "top_y")),
    "back": ((0, -1), (1, 1), ("right_x", "top_y")),
    "top": ((0, 1), (2, -1), ("left_x", "back_z")),
    "bottom": ((0, 1), (2, 1), ("left_x", "front_z")),
    "left": ((2, 1), (1, 1), ("back_z", "top_y")),
    "right": ((2, -1), (1, 1), ("front_z", "top_y")),
}
AXES = "xyz"


def unit(axis: int, sign: int) -> npt.NDArray[np.float64]:
    out = np.zeros(3)
    out[axis] = float(sign)
    return out


def basis(face: str) -> npt.NDArray[np.float64]:
    """The rotation whose rows are the face's ``u``, its up and its outward normal."""
    if face not in FACES:
        raise ValueError(f"no face {face!r}; the faces are {list(FACES)}")
    (u_axis, u_sign), (up_axis, up_sign), _ = FACES[face]
    a, b = unit(u_axis, u_sign), unit(up_axis, up_sign)
    return np.vstack([a, b, np.cross(a, b)])


def normal(face: str) -> tuple[int, int]:
    """(axis index, sign) of a face's outward normal."""
    n = basis(face)[2]
    axis = int(np.flatnonzero(n)[0])
    return axis, int(np.sign(n[axis]))


def height_key(face: str) -> str:
    """The spec key that gives a face's sheets their height: ``x``, ``y`` or ``z``."""
    return AXES[normal(face)[0]]


def to_face(points: npt.ArrayLike, face: str) -> npt.NDArray[np.float64]:
    """Points of the build frame as (a, b, h): along the face's ``u``, its up and its normal.

    The front's rotation is the identity and leaves the points as they are, so
    what is measured on a front is measured with the arithmetic it always had.
    """
    pts = np.asarray(points, dtype=float)
    if face == "front":
        return pts
    return pts @ basis(face).T


@dataclass
class FaceFrame:
    """Where a face's drawing lies in the build frame: its face and its origin."""

    #: Which face: a key of ``FACES``.
    face: str
    #: The build-frame coordinate of the drawing's ``u`` = 0 on the ``u`` axis.
    u0: float
    #: The build-frame coordinate of its ``v`` = 0 on the up axis.
    v0: float

    def offsets(self, center: npt.ArrayLike) -> tuple[float, float]:
        """(du, dv): a drawing point (u, v) lies at a = u + du, b = dv - v, center taken off.

        ``a`` and ``b`` are the point's build-frame position less *center*,
        measured along the face's ``u`` and up axes.
        """
        (u_axis, u_sign), (up_axis, up_sign), _ = FACES[self.face]
        c = np.asarray(center, dtype=float)
        if self.face == "front":
            # the front keeps the arithmetic the builder always wrote it with
            return self.u0 - float(c[0]), self.v0 - float(c[1])
        return u_sign * (self.u0 - float(c[u_axis])), up_sign * (self.v0 - float(c[up_axis]))

    def embed(
        self, ab: npt.ArrayLike, center: npt.ArrayLike, height: float
    ) -> npt.NDArray[np.float64]:
        """Build-frame positions of (a, b) points of this face lying at *height* on its normal."""
        (u_axis, u_sign), (up_axis, up_sign), _ = FACES[self.face]
        n_axis, _ = normal(self.face)
        c = np.asarray(center, dtype=float)
        pts = np.asarray(ab, dtype=float)
        out = np.empty((len(pts), 3))
        out[:, u_axis] = (
            pts[:, 0] + float(c[u_axis]) if u_sign > 0 else float(c[u_axis]) - pts[:, 0]
        )
        out[:, up_axis] = (
            pts[:, 1] + float(c[up_axis]) if up_sign > 0 else float(c[up_axis]) - pts[:, 1]
        )
        out[:, n_axis] = float(height)
        return out

    def normals(self, count: int) -> npt.NDArray[np.float64]:
        """*count* copies of the face's outward normal."""
        return np.tile(basis(self.face)[2], (count, 1))

    def record(self) -> dict[str, float]:
        """The two numbers that place the drawing, under the face's own keys."""
        keys = FACES[self.face][2]
        return {keys[0]: self.u0, keys[1]: self.v0}


def face_frame(face: str, numbers: Mapping[str, float]) -> FaceFrame:
    """A FaceFrame from ``{key: value}`` written under the face's own keys."""
    if face not in FACES:
        raise ValueError(f"no face {face!r}; the faces are {list(FACES)}")
    keys = FACES[face][2]
    missing = [k for k in keys if k not in numbers]
    extra = sorted(set(numbers) - set(keys) - {"note"})
    if missing or extra:
        raise ValueError(f"the {face} frame takes {list(keys)}; got {sorted(numbers)}")
    return FaceFrame(face, float(numbers[keys[0]]), float(numbers[keys[1]]))


def to_drawing(
    points: npt.ArrayLike, frame: FaceFrame, center: npt.ArrayLike
) -> npt.NDArray[np.float64]:
    """(u, v, h) of build-frame points relative to *center*: where a drawing of the face puts them.

    *points* are positions less *center*, as a model stores them; ``h`` is the
    height along the face's normal, center taken off.
    """
    abh = to_face(points, frame.face)
    du, dv = frame.offsets(center)
    return np.column_stack([abh[:, 0] - du, dv - abh[:, 1], abh[:, 2]])
