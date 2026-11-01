"""Solution analytique exacte du problème de Kepler (mouvement relatif).

La propagation utilise la formulation en *variable universelle* (fonctions de
Stumpff et coefficients de Lagrange f, g). Elle couvre de façon uniforme les
orbites elliptiques, paraboliques et hyperboliques.

Référence : H. D. Curtis, *Orbital Mechanics for Engineering Students*,
algorithmes 3.3 et 3.4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .etat import Etat


# --------------------------------------------------------------- éléments
@dataclass(frozen=True)
class ElementsOrbitaux:
    """Grandeurs caractéristiques de l'orbite relative."""

    energie: float               # énergie massique (J/kg)
    moment_cinetique: float      # h = x*vy - y*vx (m²/s)
    excentricite: float
    demi_grand_axe: float        # m (négatif pour une hyperbole, inf pour une parabole)
    periode: float               # s (inf si l'orbite n'est pas liée)
    periastre: float             # distance minimale (m)

    @property
    def liee(self) -> bool:
        return self.energie < 0

    @property
    def nature(self) -> str:
        if self.excentricite < 1e-9:
            return "cercle"
        if self.excentricite < 1 - 1e-9:
            return "ellipse"
        if self.excentricite <= 1 + 1e-9:
            return "parabole"
        return "hyperbole"


def elements_orbitaux(e: Etat, mu: float) -> ElementsOrbitaux:
    r, v = e.distance, e.vitesse
    energie = 0.5 * v * v - mu / r
    h = e.x * e.vy - e.y * e.vx
    exc = math.sqrt(max(0.0, 1 + 2 * energie * h * h / (mu * mu)))
    if energie == 0:
        a, periode = math.inf, math.inf
    else:
        a = -mu / (2 * energie)
        periode = 2 * math.pi * math.sqrt(a ** 3 / mu) if a > 0 else math.inf
    periastre = h * h / (mu * (1 + exc))
    return ElementsOrbitaux(energie, h, exc, a, periode, periastre)


# ------------------------------------------------------ fonctions de Stumpff
def _stumpff_c(z: float) -> float:
    if abs(z) < 1e-3:  # développement en série : évite la perte de précision
        return 0.5 - z / 24 + z * z / 720 - z ** 3 / 40320
    if z > 0:
        return (1 - math.cos(math.sqrt(z))) / z
    return (math.cosh(math.sqrt(-z)) - 1) / (-z)


def _stumpff_s(z: float) -> float:
    if abs(z) < 1e-3:
        return 1 / 6 - z / 120 + z * z / 5040 - z ** 3 / 362880
    if z > 0:
        s = math.sqrt(z)
        return (s - math.sin(s)) / s ** 3
    s = math.sqrt(-z)
    return (math.sinh(s) - s) / s ** 3


# ------------------------------------------------------------ propagation
def propager(e0: Etat, t: float, mu: float, tol: float = 1e-12, iter_max: int = 100) -> Etat:
    """État exact au temps ``t`` à partir de l'état initial ``e0``."""
    if t == 0:
        return e0
    r0 = e0.distance
    vr0 = (e0.x * e0.vx + e0.y * e0.vy) / r0
    alpha = 2 / r0 - e0.vitesse ** 2 / mu
    sq_mu = math.sqrt(mu)

    # Pour une orbite liée, on se ramène à une seule période (meilleure convergence).
    if alpha > 0:
        periode = 2 * math.pi / math.sqrt(mu * alpha ** 3)
        t = math.fmod(t, periode)

    chi = sq_mu * abs(alpha) * t if alpha != 0 else sq_mu * t / r0
    for _ in range(iter_max):
        z = alpha * chi * chi
        c, s = _stumpff_c(z), _stumpff_s(z)
        f = (r0 * vr0 / sq_mu * chi * chi * c
             + (1 - alpha * r0) * chi ** 3 * s + r0 * chi - sq_mu * t)
        df = (r0 * vr0 / sq_mu * chi * (1 - z * s)
              + (1 - alpha * r0) * chi * chi * c + r0)
        delta = f / df
        chi -= delta
        if abs(delta) < tol * max(1.0, abs(chi)):
            break
    else:
        raise RuntimeError("L'équation de Kepler n'a pas convergé")

    z = alpha * chi * chi
    c, s = _stumpff_c(z), _stumpff_s(z)
    f = 1 - chi * chi / r0 * c
    g = t - chi ** 3 * s / sq_mu
    x, y = f * e0.x + g * e0.vx, f * e0.y + g * e0.vy
    r = math.hypot(x, y)
    df = sq_mu / (r * r0) * (z * chi * s - chi)
    dg = 1 - chi * chi / r * c
    return Etat(x, y, df * e0.x + dg * e0.vx, df * e0.y + dg * e0.vy)
