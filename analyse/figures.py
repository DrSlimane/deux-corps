"""Génère les figures (PNG 300 dpi + PDF vectoriel) et les données (CSV) pour l'article.

Usage (depuis la racine du projet) :
    pip install matplotlib
    python analyse/figures.py            # écrit dans figures/

Figures produites :
    fig1_derive_energie   erreur relative d'énergie |ΔE/E0| en fonction du temps
    fig2_erreur_position  écart à la solution exacte de Kepler en fonction du temps
    fig3_convergence      erreur après une période en fonction du pas h (ordre des méthodes)
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from deux_corps.physique import Parametres, Simulation  # noqa: E402

SORTIE = RACINE / "figures"

# Cas de référence : conditions par défaut du programme (ellipse e ≈ 0.46)
CAS = dict(masse=10.0, masse2=0.0, x0=-100.0, y0=0.0, vx0=0.0, vy0=60.0)

# Une couleur + un style de trait + un marqueur par méthode : lisible en
# noir et blanc et pour les daltoniens (la couleur ne porte jamais seule l'info).
STYLES = {
    "Runge-Kutta 4":  dict(color="#2a78d6", ls="-",  marker="o"),
    "Verlet-vitesse": dict(color="#eb6834", ls="--", marker="s"),
    "Euler":          dict(color="#1baf7a", ls=":",  marker="^"),
}

plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#e3e3e3",
    "grid.linewidth": 0.6,
    "axes.edgecolor": "#555555",
    "legend.frameon": False,
    "lines.linewidth": 1.6,
    "savefig.bbox": "tight",
})


def periode_reference() -> float:
    return Simulation(Parametres(**CAS)).elements().periode


def serie_temporelle(methode: str, h: float, duree: float, nb_mesures: int = 400):
    """Retourne (t, |ΔE/E0|, erreur de position) échantillonnés au cours du temps."""
    sim = Simulation(Parametres(**CAS, pas=h, integrateur=methode))
    pas_total = round(duree / h)
    bloc = max(1, pas_total // nb_mesures)
    t, de, dr = [], [], []
    while sim.temps < duree - 0.5 * h and not sim.collision:
        sim.avancer(bloc, enregistrer_tous_les=bloc)
        t.append(sim.temps)
        de.append(abs(sim.derive_energie()))
        dr.append(sim.erreur_position())
    return t, de, dr


def erreur_apres_une_periode(methode: str, n: int, periode: float) -> float:
    sim = Simulation(Parametres(**CAS, pas=periode / n, integrateur=methode))
    sim.avancer(n)
    return math.hypot(sim.etat.x - CAS["x0"], sim.etat.y - CAS["y0"])


def enregistrer(fig, nom: str) -> None:
    for ext in ("png", "pdf"):
        fig.savefig(SORTIE / f"{nom}.{ext}", dpi=300)
    plt.close(fig)


def ecrire_csv(nom: str, entetes: list[str], lignes) -> None:
    with open(SORTIE / f"{nom}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(entetes)
        w.writerows(lignes)


def main() -> None:
    SORTIE.mkdir(exist_ok=True)
    T = periode_reference()
    h, nb_periodes = 1e-3, 20
    print(f"Période de référence T = {T:.6f} s ; h = {h} s ; {nb_periodes} périodes")

    # ---------------------------------------------------------- fig 1 et 2
    series = {m: serie_temporelle(m, h, nb_periodes * T) for m in STYLES}

    for num, (indice, nom, ylabel) in enumerate([
        (1, "fig1_derive_energie", "Erreur relative d'énergie  |ΔE / E₀|"),
        (2, "fig2_erreur_position", "Écart à la solution exacte  |r − r_Kepler|  (m)"),
    ], start=1):
        fig, ax = plt.subplots(figsize=(6.0, 3.8))
        lignes_csv = []
        for m, st in STYLES.items():
            t, de, dr = series[m]
            y = de if indice == 1 else dr
            y = [max(v, 1e-16) for v in y]  # échelle log : pas de zéro exact
            ax.plot([ti / T for ti in t], y, color=st["color"], ls=st["ls"],
                    marker=st["marker"], markevery=max(1, len(t) // 10), markersize=5,
                    label=m)
            lignes_csv += [(m, f"{ti:.6f}", f"{yi:.6e}") for ti, yi in zip(t, y)]
        ax.set_yscale("log")
        ax.set_xlabel("Temps  t / T  (nombre de périodes)")
        ax.set_ylabel(ylabel)
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=9,
                  handlelength=2.6, borderaxespad=0.2)
        ax.text(1.0, 1.10, f"e = 0,46 ; h = {h:g} s".replace(".", ","), transform=ax.transAxes,
                ha="right", fontsize=9, color="#555555")
        enregistrer(fig, nom)
        ecrire_csv(nom, ["methode", "t_s", "valeur"], lignes_csv)
        print(f"  {nom} : ok")

    # ---------------------------------------------------------------- fig 3
    valeurs_n = [50, 100, 200, 400, 800, 1600, 3200, 6400, 12800]
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    lignes_csv = []
    for m, st in STYLES.items():
        hs, errs = [], []
        for n in valeurs_n:
            err = erreur_apres_une_periode(m, n, T)
            hs.append(T / n)
            errs.append(max(err, 1e-16))
            lignes_csv.append((m, n, f"{T / n:.6e}", f"{err:.6e}"))
        ax.plot(hs, errs, color=st["color"], ls=st["ls"], marker=st["marker"],
                markersize=6, label=m)

    # Droites de référence de pente 1, 2 et 4, ancrées sur les données.
    h_ref = [T / valeurs_n[2], T / valeurs_n[-1]]
    for ordre, (m, ancre_n) in {1: ("Euler", 2), 2: ("Verlet-vitesse", 2), 4: ("Runge-Kutta 4", 2)}.items():
        e0 = erreur_apres_une_periode(m, valeurs_n[ancre_n], T) * 3
        ys = [e0 * (hh / h_ref[0]) ** ordre for hh in h_ref]
        ax.plot(h_ref, ys, color="#888888", lw=0.9, ls="-")
        ax.annotate(f"pente {ordre}", (h_ref[1], ys[1]), xytext=(4, -2),
                    textcoords="offset points", fontsize=8, color="#555555")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.invert_xaxis()
    ax.set_xlabel("Pas de temps  h  (s)")
    ax.set_ylabel("Erreur de position après une période (m)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=9,
              handlelength=2.6, borderaxespad=0.2)
    enregistrer(fig, "fig3_convergence")
    ecrire_csv("fig3_convergence", ["methode", "N_pas_par_periode", "h_s", "erreur_m"], lignes_csv)
    print("  fig3_convergence : ok")

    # Pentes mesurées (à citer dans l'article)
    print("\nOrdres mesurés (pente entre N=400 et N=3200) :")
    for m in STYLES:
        e1 = erreur_apres_une_periode(m, 400, T)
        e2 = erreur_apres_une_periode(m, 3200, T)
        print(f"  {m:15s} {math.log(e1 / e2) / math.log(8):.2f}")


if __name__ == "__main__":
    main()
