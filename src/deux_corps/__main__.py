"""Point d'entrée : ``python -m deux_corps`` ou la commande ``deux-corps``."""

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from .interface.fenetre_principale import FenetrePrincipale

    app = QApplication(sys.argv)
    fenetre = FenetrePrincipale()
    fenetre.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
