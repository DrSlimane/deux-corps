"""Fenêtre principale : panneau de paramètres, zone de dessin et commandes."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..physique import INTEGRATEURS, Parametres, Simulation
from .controles import ChampNumerique
from .zone_trajectoire import ZoneTrajectoire


class FenetrePrincipale(QMainWindow):
    """Assemble l'interface et pilote la simulation via un minuteur."""

    INTERVALLE_MS = 16  # ~60 images/s

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(
            f"Problème à deux corps v{__version__} — S. Mouchou, A. Aaouine, Y. Es-bai"
        )
        self.setMinimumSize(1000, 600)

        self.simulation = Simulation(Parametres())
        self.zone = ZoneTrajectoire(self.simulation)

        self.minuteur = QTimer(self)
        self.minuteur.setInterval(self.INTERVALLE_MS)
        self.minuteur.timeout.connect(self._image_suivante)

        central = QWidget()
        disposition = QHBoxLayout(central)
        disposition.addWidget(self._construire_panneau())
        disposition.addWidget(self.zone, stretch=1)
        self.setCentralWidget(central)

        self._rafraichir()

    # ------------------------------------------------------- construction
    def _construire_panneau(self) -> QWidget:
        p = self.simulation.parametres

        self.champ_masse = ChampNumerique("Masse m1 (×1e15 kg)", 0, 1000, p.masse)
        self.champ_masse2 = ChampNumerique("Masse m2 (×1e15 kg, 0 = m1 fixe)", 0, 1000, p.masse2)
        self.champ_x = ChampNumerique("Position relative x", -500, 500, p.x0, "m")
        self.champ_y = ChampNumerique("Position relative y", -500, 500, p.y0, "m")
        self.champ_vx = ChampNumerique("Vitesse relative Vx", -300, 300, p.vx0, "m/s")
        self.champ_vy = ChampNumerique("Vitesse relative Vy", -300, 300, p.vy0, "m/s")

        groupe_ci = QGroupBox("Conditions initiales (corps 2 / corps 1)")
        v = QVBoxLayout(groupe_ci)
        champs = (self.champ_masse, self.champ_masse2, self.champ_x, self.champ_y,
                  self.champ_vx, self.champ_vy)
        for champ in champs:
            champ.valeurModifiee.connect(self._parametres_modifies)
            v.addWidget(champ)

        self.choix_integrateur = QComboBox()
        self.choix_integrateur.addItems(INTEGRATEURS)
        self.choix_integrateur.currentTextChanged.connect(self._parametres_modifies)

        self.champ_pas = ChampNumerique("Pas de temps h", 1e-5, 0.1, p.pas, "s", decimales=5, pas=1e-4)
        self.champ_pas.valeurModifiee.connect(self._parametres_modifies)

        self.champ_vitesse = QSpinBox()
        self.champ_vitesse.setRange(1, 5000)
        self.champ_vitesse.setValue(100)
        self.champ_vitesse.setToolTip("Nombre de pas de calcul effectués à chaque image")

        groupe_num = QGroupBox("Méthode numérique")
        f = QFormLayout(groupe_num)
        f.addRow("Intégrateur :", self.choix_integrateur)
        f.addRow(self.champ_pas)
        f.addRow("Pas / image :", self.champ_vitesse)

        self.case_exacte = QCheckBox("Afficher la solution exacte")
        self.case_exacte.setChecked(True)
        self.case_exacte.toggled.connect(self._basculer_exacte)
        f.addRow(self.case_exacte)

        self.bouton_go = QPushButton("&Go !")
        self.bouton_go.setToolTip("Lancer / reprendre la simulation")
        self.bouton_go.setDefault(True)
        self.bouton_go.clicked.connect(self.demarrer)
        self.bouton_pause = QPushButton("&Pause")
        self.bouton_pause.setToolTip("Mettre la simulation en pause")
        self.bouton_pause.clicked.connect(self.pause)
        self.bouton_arret = QPushButton("&Arrêt")
        self.bouton_arret.setToolTip("Arrêter et revenir aux conditions initiales")
        self.bouton_arret.clicked.connect(self.arreter)
        for b in (self.bouton_go, self.bouton_pause, self.bouton_arret):
            b.setCursor(Qt.PointingHandCursor)

        boutons = QHBoxLayout()
        boutons.addWidget(self.bouton_go)
        boutons.addWidget(self.bouton_pause)
        boutons.addWidget(self.bouton_arret)

        self.infos = QLabel()
        self.infos.setTextFormat(Qt.RichText)
        groupe_infos = QGroupBox("Mesures")
        QVBoxLayout(groupe_infos).addWidget(self.infos)

        panneau = QWidget()
        panneau.setFixedWidth(280)
        col = QVBoxLayout(panneau)
        col.setContentsMargins(0, 0, 0, 0)
        col.addWidget(groupe_ci)
        col.addWidget(groupe_num)
        col.addLayout(boutons)
        col.addWidget(groupe_infos)
        col.addStretch()
        col.addWidget(QLabel("<i>Molette : zoom</i>"))
        return panneau

    # ----------------------------------------------------------- actions
    def demarrer(self) -> None:
        if not self.simulation.collision:
            self.minuteur.start()

    def pause(self) -> None:
        self.minuteur.stop()

    def arreter(self) -> None:
        self.minuteur.stop()
        self.simulation.reinitialiser()
        self._rafraichir()

    # --------------------------------------------------------- internes
    def _parametres_modifies(self, *_):
        """Toute modification de paramètre relance la simulation depuis le départ."""
        p = self.simulation.parametres
        p.masse = self.champ_masse.valeur()
        p.masse2 = self.champ_masse2.valeur()
        p.x0, p.y0 = self.champ_x.valeur(), self.champ_y.valeur()
        p.vx0, p.vy0 = self.champ_vx.valeur(), self.champ_vy.valeur()
        p.pas = self.champ_pas.valeur()
        p.integrateur = self.choix_integrateur.currentText()
        self.arreter()

    def _image_suivante(self) -> None:
        n = self.champ_vitesse.value()
        # On n'enregistre qu'environ 20 points par image pour garder un dessin fluide.
        self.simulation.avancer(n, enregistrer_tous_les=max(1, n // 20))
        if self.simulation.collision:
            self.minuteur.stop()
        self._rafraichir()

    def _basculer_exacte(self, actif: bool) -> None:
        self.zone.afficher_exacte = actif
        self.zone.update()

    def _rafraichir(self) -> None:
        s = self.simulation
        e = s.etat
        lignes = [
            f"t = {s.temps:.3f} s",
            f"r = {e.distance:.2f} m &nbsp; |v| = {e.vitesse:.2f} m/s",
            f"E = {s.energie():.4g} J/kg",
            f"dérive ΔE/E₀ = {s.derive_energie():.2e}",
            f"écart / exacte = {s.erreur_position():.2e} m",
        ]
        el = s.elements()
        if el is not None:
            periode = f"{el.periode:.3f} s" if el.liee else "∞"
            lignes += [
                "<br><b>Orbite exacte</b>",
                f"{el.nature}, e = {el.excentricite:.4f}",
                f"périastre = {el.periastre:.2f} m",
                f"période T = {periode}",
            ]
        self.infos.setText("<br>".join(lignes))
        self.zone.update()
