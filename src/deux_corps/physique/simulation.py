"""Moteur de simulation du problème à deux corps.

Réduction au problème à un corps
--------------------------------
Pour deux masses m1 et m2, on intègre le mouvement *relatif*
r = r2 - r1, qui obéit à  d²r/dt² = -G (m1 + m2) r / |r|³.
Les positions réelles dans le référentiel du centre de masse s'en déduisent :

    r1 = -m2 / (m1 + m2) · r        r2 = m1 / (m1 + m2) · r

Avec m2 = 0 on retrouve le modèle d'origine (corps central fixe).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .constantes import RAYON_COLLISION
from .etat import Etat
from .forces import parametre_gravitationnel
from .integrateurs import INTEGRATEURS
from .kepler import ElementsOrbitaux, elements_orbitaux, propager

Point = tuple[float, float]


@dataclass
class Parametres:
    """Conditions initiales (mouvement relatif du corps 2 par rapport au corps 1)."""

    masse: float = 10.0          # m1, en unités de 1e15 kg
    masse2: float = 0.0          # m2, en unités de 1e15 kg (0 = particule test)
    x0: float = -100.0           # m
    y0: float = 0.0              # m
    vx0: float = 0.0             # m/s
    vy0: float = 60.0            # m/s
    pas: float = 1e-3            # pas de temps h (s)
    integrateur: str = "Runge-Kutta 4"

    def etat_initial(self) -> Etat:
        return Etat(self.x0, self.y0, self.vx0, self.vy0)

    @property
    def masse_totale(self) -> float:
        return self.masse + self.masse2

    def fractions(self) -> tuple[float, float]:
        """(m1/M, m2/M) : servent à placer chaque corps autour du centre de masse."""
        m = self.masse_totale
        return (1.0, 0.0) if m == 0 else (self.masse / m, self.masse2 / m)


class Simulation:
    """Intègre le mouvement relatif et garde l'historique des positions.

    Indépendante de toute interface graphique : utilisable en console,
    dans des tests, des scripts d'analyse ou un notebook.
    """

    #: Nombre maximal de points conservés (au-delà, on sous-échantillonne).
    MAX_POINTS = 200_000

    def __init__(self, parametres: Parametres | None = None) -> None:
        self.parametres = parametres or Parametres()
        self.reinitialiser()

    # ------------------------------------------------------------------ état
    def reinitialiser(self) -> None:
        """Revient aux conditions initiales et efface la trajectoire."""
        p = self.parametres
        if p.integrateur not in INTEGRATEURS:
            raise ValueError(f"Intégrateur inconnu : {p.integrateur!r}")
        self._integrer = INTEGRATEURS[p.integrateur]
        self._mu = parametre_gravitationnel(p.masse_totale)
        self.etat_initial = p.etat_initial()
        self.etat = self.etat_initial
        self.temps = 0.0
        self.collision = self.etat.distance < RAYON_COLLISION
        self.trajectoire: list[Point] = [(self.etat.x, self.etat.y)]
        self.energie_initiale = self.energie()

    @property
    def mu(self) -> float:
        """Paramètre gravitationnel G·(m1 + m2) (m³/s²)."""
        return self._mu

    # ------------------------------------------------------------ mesures
    def energie(self) -> float:
        """Énergie massique du mouvement relatif E = v²/2 - mu/r (J/kg)."""
        r = self.etat.distance
        if r == 0:
            return float("-inf")
        return 0.5 * self.etat.vitesse ** 2 - self._mu / r

    def derive_energie(self) -> float:
        """Écart relatif d'énergie depuis le départ (indicateur de précision)."""
        e0 = self.energie_initiale
        if e0 == 0 or self.collision:
            return 0.0
        return (self.energie() - e0) / abs(e0)

    def elements(self) -> ElementsOrbitaux | None:
        """Éléments de l'orbite exacte définie par les conditions initiales."""
        if self._mu == 0 or self.etat_initial.distance == 0:
            return None
        return elements_orbitaux(self.etat_initial, self._mu)

    def solution_exacte(self, t: float | None = None) -> Etat:
        """Position/vitesse relatives exactes (Kepler) au temps t (par défaut : maintenant)."""
        return propager(self.etat_initial, self.temps if t is None else t, self._mu)

    def erreur_position(self) -> float:
        """Distance (m) entre la solution numérique et la solution exacte."""
        if self._mu == 0 or self.collision:
            return 0.0
        ex = self.solution_exacte()
        return math.hypot(self.etat.x - ex.x, self.etat.y - ex.y)

    def orbite_exacte(self, nb_points: int = 400) -> list[Point]:
        """Points de l'orbite exacte : une période complète si l'orbite est liée,
        sinon la portion parcourue jusqu'au temps actuel."""
        el = self.elements()
        if el is None or el.moment_cinetique == 0:
            return []
        duree = el.periode if el.liee else self.temps
        if duree <= 0:
            return []
        pts = []
        for k in range(nb_points + 1):
            e = propager(self.etat_initial, duree * k / nb_points, self._mu)
            pts.append((e.x, e.y))
        return pts

    def positions_corps(self, x: float, y: float) -> tuple[Point, Point]:
        """Positions des deux corps (référentiel du centre de masse) pour un écart relatif (x, y)."""
        f1, f2 = self.parametres.fractions()
        return (-f2 * x, -f2 * y), (f1 * x, f1 * y)

    # ------------------------------------------------------------- calcul
    def avancer(self, nb_pas: int, enregistrer_tous_les: int = 1) -> None:
        """Effectue ``nb_pas`` pas d'intégration.

        Un point est ajouté à la trajectoire tous les ``enregistrer_tous_les`` pas,
        pour limiter la mémoire et le temps de dessin.
        """
        if self.collision:
            return
        h = self.parametres.pas
        mu = self._mu
        integrer = self._integrer
        etat = self.etat
        points = self.trajectoire

        for i in range(1, nb_pas + 1):
            etat = integrer(etat, h, mu)
            if etat.distance < RAYON_COLLISION:
                self.collision = True
                points.append((etat.x, etat.y))
                self.temps += i * h
                self.etat = etat
                return
            if i % enregistrer_tous_les == 0:
                points.append((etat.x, etat.y))

        self.etat = etat
        self.temps += nb_pas * h
        if len(points) > self.MAX_POINTS:
            self.trajectoire = points[::2]
