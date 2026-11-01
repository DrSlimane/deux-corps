"""Constantes physiques et unités utilisées par la simulation."""

#: Constante de gravitation universelle (m^3 kg^-1 s^-2).
G: float = 6.674_30e-11

#: Unité de masse affichée dans l'interface : la masse saisie est multipliée par 1e15 kg.
UNITE_MASSE: float = 1e15

#: En dessous de cette distance (m) au corps central, on considère qu'il y a collision.
RAYON_COLLISION: float = 1.0
