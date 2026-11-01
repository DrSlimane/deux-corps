"""Widgets de saisie réutilisables (équivalent de la classe ``Controle`` d'origine)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QLabel, QVBoxLayout, QWidget


class ChampNumerique(QWidget):
    """Une étiquette au-dessus d'un champ numérique avec bornes, unité et info-bulle."""

    valeurModifiee = Signal(float)

    def __init__(
        self,
        libelle: str,
        minimum: float,
        maximum: float,
        valeur: float,
        unite: str = "",
        decimales: int = 2,
        pas: float = 1.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._champ = QDoubleSpinBox()
        self._champ.setDecimals(decimales)
        self._champ.setRange(minimum, maximum)
        self._champ.setSingleStep(pas)
        self._champ.setValue(valeur)
        if unite:
            self._champ.setSuffix(f" {unite}")
        self._champ.setToolTip(f"Valeur entre {minimum:g} et {maximum:g}")
        self._champ.valueChanged.connect(self.valeurModifiee)

        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.setSpacing(2)
        disposition.addWidget(QLabel(libelle))
        disposition.addWidget(self._champ)
        self.setFocusProxy(self._champ)

    def valeur(self) -> float:
        return self._champ.value()

    def definir_valeur(self, valeur: float) -> None:
        self._champ.setValue(valeur)
