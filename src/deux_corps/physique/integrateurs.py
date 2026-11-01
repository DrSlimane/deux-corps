"""Schémas d'intégration numérique des équations du mouvement.

Chaque intégrateur est une fonction ``(etat, h, mu) -> nouvel_etat``.
Le dictionnaire :data:`INTEGRATEURS` permet de les choisir par leur nom.
"""

from __future__ import annotations

from typing import Callable

from .etat import Etat
from .forces import acceleration_gravitationnelle as accel

Integrateur = Callable[[Etat, float, float], Etat]


def euler(e: Etat, h: float, mu: float) -> Etat:
    """Euler explicite (ordre 1) — donné pour comparaison, il dérive vite."""
    ax, ay = accel(e.x, e.y, mu)
    return Etat(e.x + h * e.vx, e.y + h * e.vy, e.vx + h * ax, e.vy + h * ay)


def runge_kutta_4(e: Etat, h: float, mu: float) -> Etat:
    """Runge-Kutta classique d'ordre 4 sur le système (x, y, vx, vy)."""
    # k1
    ax1, ay1 = accel(e.x, e.y, mu)
    # k2
    x2, y2 = e.x + 0.5 * h * e.vx, e.y + 0.5 * h * e.vy
    vx2, vy2 = e.vx + 0.5 * h * ax1, e.vy + 0.5 * h * ay1
    ax2, ay2 = accel(x2, y2, mu)
    # k3
    x3, y3 = e.x + 0.5 * h * vx2, e.y + 0.5 * h * vy2
    vx3, vy3 = e.vx + 0.5 * h * ax2, e.vy + 0.5 * h * ay2
    ax3, ay3 = accel(x3, y3, mu)
    # k4
    x4, y4 = e.x + h * vx3, e.y + h * vy3
    vx4, vy4 = e.vx + h * ax3, e.vy + h * ay3
    ax4, ay4 = accel(x4, y4, mu)

    s = h / 6.0
    return Etat(
        e.x + s * (e.vx + 2 * vx2 + 2 * vx3 + vx4),
        e.y + s * (e.vy + 2 * vy2 + 2 * vy3 + vy4),
        e.vx + s * (ax1 + 2 * ax2 + 2 * ax3 + ax4),
        e.vy + s * (ay1 + 2 * ay2 + 2 * ay3 + ay4),
    )


def verlet_vitesse(e: Etat, h: float, mu: float) -> Etat:
    """Verlet-vitesse (ordre 2, symplectique) : conserve très bien l'énergie à long terme."""
    ax, ay = accel(e.x, e.y, mu)
    vx_demi = e.vx + 0.5 * h * ax
    vy_demi = e.vy + 0.5 * h * ay
    x, y = e.x + h * vx_demi, e.y + h * vy_demi
    ax, ay = accel(x, y, mu)
    return Etat(x, y, vx_demi + 0.5 * h * ax, vy_demi + 0.5 * h * ay)


INTEGRATEURS: dict[str, Integrateur] = {
    "Runge-Kutta 4": runge_kutta_4,
    "Verlet-vitesse": verlet_vitesse,
    "Euler": euler,
}
