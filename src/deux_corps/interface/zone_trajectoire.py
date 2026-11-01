"""Zone de dessin : repère, deux corps, trajectoires numériques et orbite exacte."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QWheelEvent
from PySide6.QtWidgets import QWidget

from ..physique.constantes import UNITE_MASSE
from ..physique.simulation import Point, Simulation

COULEUR_CORPS1 = QColor(30, 80, 200)
COULEUR_CORPS2 = QColor(220, 30, 30)
COULEUR_EXACTE = QColor(20, 150, 70)


class ZoneTrajectoire(QWidget):
    """Affiche la simulation dans le référentiel du centre de masse.

    Molette de la souris = zoom. On dessine les points déjà calculés au lieu
    de recalculer toute la trajectoire à chaque image (comme le faisait la
    version C++).
    """

    ZOOM_MIN, ZOOM_MAX = 0.05, 50.0

    def __init__(self, simulation: Simulation, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.simulation = simulation
        self.echelle = 1.0  # pixels par mètre
        self.afficher_exacte = True
        self._cache_exacte: tuple[object, list[Point]] | None = None
        self.setMinimumSize(500, 400)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("white"))
        self.setPalette(palette)

    # ------------------------------------------------------------ repère
    def vers_ecran(self, x: float, y: float) -> QPointF:
        """Convertit des coordonnées physiques (m) en pixels (axe y vers le haut)."""
        return QPointF(self.width() / 2 + x * self.echelle, self.height() / 2 - y * self.echelle)

    def _graduation(self) -> float:
        """Choisit un pas de grille « rond » (1, 2, 5 × 10^n m) d'environ 60 px."""
        cible = 60 / self.echelle
        puissance = 10 ** math.floor(math.log10(cible))
        for k in (1, 2, 5, 10):
            if k * puissance >= cible:
                return k * puissance
        return 10 * puissance

    # ------------------------------------------------------------ dessin
    def paintEvent(self, _event) -> None:  # noqa: N802 (nom imposé par Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self._dessiner_grille(p)
        if self.afficher_exacte:
            self._dessiner_orbite_exacte(p)
        self._dessiner_trajectoires(p)
        self._dessiner_legende(p)
        p.end()

    def _dessiner_grille(self, p: QPainter) -> None:
        w, h = self.width(), self.height()
        pas = self._graduation()
        cx, cy = w / 2, h / 2
        nx = int(cx / (pas * self.echelle)) + 1
        ny = int(cy / (pas * self.echelle)) + 1

        p.setPen(QPen(QColor(220, 220, 220), 1, Qt.DotLine))
        for i in range(-nx, nx + 1):
            X = cx + i * pas * self.echelle
            p.drawLine(QPointF(X, 0), QPointF(X, h))
        for j in range(-ny, ny + 1):
            Y = cy + j * pas * self.echelle
            p.drawLine(QPointF(0, Y), QPointF(w, Y))

        p.setPen(QPen(Qt.black, 1))
        p.drawLine(QPointF(0, cy), QPointF(w, cy))
        p.drawLine(QPointF(cx, 0), QPointF(cx, h))

        p.setFont(QFont("Sans", 8))
        p.setPen(QColor(90, 90, 90))
        for i in range(-nx, nx + 1):
            X = cx + i * pas * self.echelle
            if i and X < w - 60:  # laisse la place au libellé « x (m) »
                p.drawText(QPointF(X + 3, cy - 4), f"{i * pas:g}")
        for j in range(-ny, ny + 1):
            Y = cy - j * pas * self.echelle
            if j and Y > 30:  # laisse la place au libellé « y (m) »
                p.drawText(QPointF(cx + 4, Y - 3), f"{j * pas:g}")
        p.drawText(QPointF(w - 30, cy - 4), "x (m)")
        p.drawText(QPointF(cx + 4, 14), "y (m)")

    def _chemin(self, points: list[Point], corps: int) -> QPainterPath:
        """Trajet du corps 1 ou 2, à partir des positions relatives."""
        sim = self.simulation
        chemin = QPainterPath()
        for k, (x, y) in enumerate(points):
            pos = sim.positions_corps(x, y)[corps - 1]
            q = self.vers_ecran(*pos)
            if k == 0:
                chemin.moveTo(q)
            else:
                chemin.lineTo(q)
        return chemin

    def _orbite_exacte(self) -> list[Point]:
        sim = self.simulation
        el = sim.elements()
        # Orbite liée : ne dépend que des paramètres -> mise en cache.
        if el is not None and el.liee:
            cle = (id(sim.parametres), sim.etat_initial, sim.mu)
            if self._cache_exacte is None or self._cache_exacte[0] != cle:
                self._cache_exacte = (cle, sim.orbite_exacte())
            return self._cache_exacte[1]
        return sim.orbite_exacte(200)

    def _dessiner_orbite_exacte(self, p: QPainter) -> None:
        points = self._orbite_exacte()
        if len(points) < 2:
            return
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(COULEUR_EXACTE, 1.5, Qt.DashLine))
        p.drawPath(self._chemin(points, 2))
        if self.simulation.parametres.masse2 > 0:
            p.drawPath(self._chemin(points, 1))

    def _dessiner_trajectoires(self, p: QPainter) -> None:
        sim = self.simulation
        points = sim.trajectoire
        p.setBrush(Qt.NoBrush)
        if sim.parametres.masse2 > 0:
            p.setPen(QPen(COULEUR_CORPS1, 2))
            p.drawPath(self._chemin(points, 1))
        p.setPen(QPen(COULEUR_CORPS2, 2))
        p.drawPath(self._chemin(points, 2))

        # Centre de masse
        p.setPen(QPen(Qt.black, 1))
        o = self.vers_ecran(0, 0)
        p.drawLine(o + QPointF(-5, -5), o + QPointF(5, 5))
        p.drawLine(o + QPointF(-5, 5), o + QPointF(5, -5))

        # Corps (rayon d'affichage croissant avec la masse)
        e = sim.etat
        (x1, y1), (x2, y2) = sim.positions_corps(e.x, e.y)
        par = sim.parametres
        p.setPen(Qt.NoPen)
        p.setBrush(COULEUR_CORPS1)
        p.drawEllipse(self.vers_ecran(x1, y1), *(2 * [self._rayon(par.masse, 7)]))
        p.setBrush(QColor(0, 0, 0) if sim.collision else QColor(240, 140, 0))
        p.drawEllipse(self.vers_ecran(x2, y2), *(2 * [self._rayon(par.masse2, 5)]))

    @staticmethod
    def _rayon(masse: float, minimum: float) -> float:
        return minimum if masse <= 0 else max(minimum, min(14.0, 4 + 2 * math.log10(1 + masse)))

    def _dessiner_legende(self, p: QPainter) -> None:
        sim = self.simulation
        par = sim.parametres
        p.setFont(QFont("Sans", 10, QFont.Bold))
        p.setPen(COULEUR_CORPS1)
        p.drawText(10, 20, f"m1 = {par.masse * UNITE_MASSE:.3g} kg")
        p.setPen(COULEUR_CORPS2)
        p.drawText(10, 38, f"m2 = {par.masse2 * UNITE_MASSE:.3g} kg")
        p.setFont(QFont("Sans", 9))
        p.setPen(QColor(60, 60, 60))
        p.drawText(10, 56, f"Méthode : {par.integrateur}")
        if self.afficher_exacte:
            p.setPen(COULEUR_EXACTE)
            p.drawText(10, 72, "- - -  solution exacte (Kepler)")
        if sim.collision:
            p.setFont(QFont("Sans", 10, QFont.Bold))
            p.setPen(QColor(200, 0, 0))
            p.drawText(10, 92, "Collision !")

    # ------------------------------------------------------------- zoom
    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        facteur = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.echelle = min(self.ZOOM_MAX, max(self.ZOOM_MIN, self.echelle * facteur))
        self.update()
