"""Représentation de l'état (position, vitesse) du corps en mouvement."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Etat:
    """État du corps mobile dans le plan, le corps central étant fixé à l'origine.

    Attributs:
        x, y: position (m)
        vx, vy: vitesse (m/s)
    """

    x: float
    y: float
    vx: float
    vy: float

    @property
    def distance(self) -> float:
        """Distance au corps central (m)."""
        return math.hypot(self.x, self.y)

    @property
    def vitesse(self) -> float:
        """Norme de la vitesse (m/s)."""
        return math.hypot(self.vx, self.vy)
