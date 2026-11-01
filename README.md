# Problème à deux corps — version Python

Réécriture en Python (PySide6 / Qt 6) du programme C++/Qt
« Problème à deux corps RK V2.0 », étendue au vrai
problème à deux corps et comparée à la solution analytique de Kepler.

## Auteurs

- Slimane Mouchou
- Abderrazzak Aaouine
- Youssef Es-bai

## Modèle physique

Deux masses m1 et m2 s'attirent. On intègre le mouvement **relatif**
r = r2 − r1 :

    d²r/dt² = − G (m1 + m2) · r / |r|³

puis on place chaque corps dans le référentiel du centre de masse :

    r1 = − m2/(m1+m2) · r        r2 = m1/(m1+m2) · r

Avec **m2 = 0**, on retrouve le modèle d'origine (corps central fixe).

La **solution exacte** (formulation en variable universelle, fonctions de
Stumpff, coefficients de Lagrange f et g) sert de référence pour mesurer
l'erreur des intégrateurs numériques : Runge-Kutta 4, Verlet-vitesse et Euler.

## Installation et lancement

```bash
pip install -e .            # installe PySide6 et la commande deux-corps
deux-corps                  # ou : python -m deux_corps
```

Sans installation : `pip install PySide6`, puis `cd src` et `python -m deux_corps`.

Tests :

```bash
pip install -e ".[dev]"
pytest
```

Figures pour l'article (PNG 300 dpi + PDF vectoriel + données CSV dans `figures/`) :

```bash
pip install matplotlib
python analyse/figures.py
```

## Organisation du code

```
src/deux_corps/
├── __main__.py               point d'entrée (crée la QApplication)
├── physique/                 calcul pur, aucune dépendance à Qt
│   ├── constantes.py         G, unité de masse, rayon de collision
│   ├── etat.py               classe Etat (x, y, vx, vy)
│   ├── forces.py             accélération gravitationnelle
│   ├── integrateurs.py       Runge-Kutta 4, Verlet-vitesse, Euler
│   ├── kepler.py             solution exacte + éléments orbitaux
│   └── simulation.py         Parametres + Simulation (deux corps, énergie, erreur)
└── interface/                interface graphique PySide6
    ├── controles.py          ChampNumerique (ex-classe Controle)
    ├── zone_trajectoire.py   dessin du repère, des corps et de l'orbite exacte
    └── fenetre_principale.py fenêtre, boutons, mesures, minuteur
analyse/figures.py            génération des figures de l'article
tests/                        tests unitaires (physique et Kepler)
```

## Résultats (cas de référence : e = 0,46, T = 4,357 s)

| Méthode        | Ordre théorique | Ordre mesuré | |ΔE/E₀| après 20 T (h = 1 ms) |
|----------------|-----------------|--------------|------------------------------|
| Runge-Kutta 4  | 4               | 4,06         | ~10⁻¹² (dérive lente)        |
| Verlet-vitesse | 2               | 2,00         | ≤ 4·10⁻⁶ (borné, oscillant)  |
| Euler          | 1               | 0,88         | ~0,3 (orbite détruite)       |

- `fig1_derive_energie` : RK4 est très précis, mais son erreur d'énergie
  **croît** lentement. Celle de Verlet, plus grande, reste **bornée** : c'est la
  signature d'un intégrateur symplectique.
- `fig2_erreur_position` : écart à la solution exacte au cours du temps.
- `fig3_convergence` : erreur après une période en fonction de h, avec les
  pentes de référence 1, 2 et 4.

## Correspondance avec la version C++

| C++               | Python                                   |
|-------------------|------------------------------------------|
| `ed`              | `physique.Etat` + `physique.integrateurs`|
| `Force()`         | `physique.forces.acceleration_gravitationnelle` |
| `Trajectoire`     | `physique.Simulation` (calcul) + `interface.ZoneTrajectoire` (dessin) |
| `Controle`        | `interface.ChampNumerique`               |
| `Fenetre`, `main` | `interface.FenetrePrincipale`, `__main__`|

## Améliorations par rapport à l'original

- **Runge-Kutta 4 correct** : l'original n'appliquait RK qu'à la vitesse et
  mettait à jour la position par Euler (`x = x + h*vx`).
- **Plus de recalcul complet à chaque image** : l'original refaisait toute la
  trajectoire depuis t = 0 à chaque `paintEvent`.
- **Vrai problème à deux corps** (m2 > 0), affiché dans le référentiel du centre de masse.
- **Solution exacte de Kepler** superposée en pointillés, et écart affiché en direct.
- Éléments orbitaux affichés : nature de la conique, excentricité, périastre, période.
- Choix de l'intégrateur et du pas, vitesse d'animation réglable, zoom, détection de collision.
- Plus de variable globale ; physique séparée de l'affichage, donc testable.

## Unités

Positions en m, vitesses en m/s, masses saisies en unités de 10¹⁵ kg.
Valeurs par défaut : m1 = 10, m2 = 0, x₀ = −100 m, y₀ = 0, Vx₀ = 0, Vy₀ = 60 m/s.
