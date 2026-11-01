"""Tests de la solution exacte de Kepler et du vrai mode à deux corps."""

import math

import pytest

from deux_corps.physique import Etat, Parametres, Simulation, elements_orbitaux, propager
from deux_corps.physique.forces import parametre_gravitationnel

MU = parametre_gravitationnel(10.0)


def test_orbite_circulaire_elements():
    r = 100.0
    v = math.sqrt(MU / r)
    el = elements_orbitaux(Etat(r, 0, 0, v), MU)
    assert el.excentricite == pytest.approx(0, abs=1e-12)
    assert el.demi_grand_axe == pytest.approx(r)
    assert el.periode == pytest.approx(2 * math.pi * r / v)
    assert el.nature == "cercle"


def test_retour_au_point_initial_apres_une_periode():
    e0 = Etat(-100, 0, 0, 60)
    el = elements_orbitaux(e0, MU)
    e = propager(e0, el.periode, MU)
    assert math.hypot(e.x - e0.x, e.y - e0.y) < 1e-8


def test_troisieme_loi_de_kepler():
    """T² / a³ = 4π² / mu pour toutes les orbites liées."""
    for vy in (40, 60, 80, 100):
        el = elements_orbitaux(Etat(-100, 0, 0, vy), MU)
        assert el.periode ** 2 / el.demi_grand_axe ** 3 == pytest.approx(4 * math.pi ** 2 / MU)


@pytest.mark.parametrize("vy", [60.0, 150.0])  # ellipse puis hyperbole
def test_kepler_concorde_avec_rk4(vy):
    sim = Simulation(Parametres(vy0=vy, pas=1e-4))
    sim.avancer(30_000)
    assert sim.erreur_position() < 1e-6


def test_energie_conservee_par_solution_exacte():
    e0 = Etat(-100, 20, 5, 60)
    el0 = elements_orbitaux(e0, MU)
    for t in (0.3, 1.7, 12.5, 100.0):
        assert elements_orbitaux(propager(e0, t, MU), MU).energie == pytest.approx(el0.energie, rel=1e-9)


def test_deux_corps_centre_de_masse_fixe():
    sim = Simulation(Parametres(masse=10, masse2=5))
    sim.avancer(3000)
    (x1, y1), (x2, y2) = sim.positions_corps(sim.etat.x, sim.etat.y)
    assert 10 * x1 + 5 * x2 == pytest.approx(0, abs=1e-9)
    assert 10 * y1 + 5 * y2 == pytest.approx(0, abs=1e-9)
    # Écart entre les corps = mouvement relatif
    assert math.hypot(x2 - x1, y2 - y1) == pytest.approx(sim.etat.distance)


def test_deux_corps_periode_plus_courte():
    """Avec m2 > 0, mu = G(m1+m2) augmente : la période diminue."""
    T1 = Simulation(Parametres(masse2=0)).elements().periode
    T2 = Simulation(Parametres(masse2=5)).elements().periode
    assert T2 < T1


def test_m2_nul_redonne_le_modele_original():
    sim = Simulation(Parametres(masse2=0))
    (x1, y1), (x2, y2) = sim.positions_corps(-100, 0)
    assert (x1, y1) == (0, 0) and (x2, y2) == (-100, 0)
