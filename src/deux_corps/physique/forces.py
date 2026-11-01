"""Lois de force : attraction gravitationnelle d'un corps central fixe."""

from __future__ import annotations

import math

from .constantes import G, UNITE_MASSE


def parametre_gravitationnel(masse_affichee: float) -> float:
    """Retourne mu = G * M (m^3/s^2) pour une masse exprimée en unités de 1e15 kg.

    Pour le problème à deux corps, M est la masse totale m1 + m2.
    """
    return G * masse_affichee * UNITE_MASSE


def acceleration_gravitationnelle(x: float, y: float, mu: float) -> tuple[float, float]:
    """Accélération a = -mu * r / |r|^3 subie au point (x, y).

    Lève ZeroDivisionError si le point est exactement sur le corps central ;
    la simulation détecte la collision avant d'en arriver là.
    """
    r = math.hypot(x, y)
    facteur = -mu / (r * r * r)
    return facteur * x, facteur * y
