"""Tests de la partie physique (aucune dépendance à Qt)."""

import math

import pytest

from deux_corps.physique import INTEGRATEURS, Etat, Parametres, Simulation
from deux_corps.physique.forces import acceleration_gravitationnelle, parametre_gravitationnel


def orbite_circulaire(integrateur: str, pas: float = 1e-3) -> Simulation:
    masse, r = 10.0, 100.0
    v = math.sqrt(parametre_gravitationnel(masse) / r)
    return Simulation(Parametres(masse=masse, x0=r, y0=0, vx0=0, vy0=v, pas=pas, integrateur=integrateur))


def test_acceleration_dirigee_vers_le_centre():
    ax, ay = acceleration_gravitationnelle(10.0, 0.0, mu=100.0)
    assert ax == pytest.approx(-1.0) and ay == 0.0


@pytest.mark.parametrize("nom", ["Runge-Kutta 4", "Verlet-vitesse"])
def test_orbite_circulaire_conservee(nom):
    sim = orbite_circulaire(nom)
    periode = 2 * math.pi * 100 / sim.etat.vitesse
    sim.avancer(int(periode / sim.parametres.pas))
    assert sim.etat.distance == pytest.approx(100.0, rel=1e-3)
    assert abs(sim.derive_energie()) < 1e-4
    # Retour près du point de départ après une période
    assert math.hypot(sim.etat.x - 100, sim.etat.y) < 1.0


def test_rk4_plus_precis_qu_euler():
    derives = {}
    for nom in ("Runge-Kutta 4", "Euler"):
        sim = orbite_circulaire(nom, pas=1e-2)
        sim.avancer(1000)
        derives[nom] = abs(sim.derive_energie())
    assert derives["Runge-Kutta 4"] < derives["Euler"] / 1000


def test_collision_detectee():
    sim = Simulation(Parametres(masse=10, x0=-100, y0=0, vx0=0, vy0=0))
    sim.avancer(1_000_000)
    assert sim.collision


def test_reinitialiser():
    sim = orbite_circulaire("Runge-Kutta 4")
    sim.avancer(500)
    sim.reinitialiser()
    assert sim.temps == 0 and len(sim.trajectoire) == 1
    assert sim.etat == Etat(100.0, 0.0, 0.0, sim.parametres.vy0)


def test_integrateur_inconnu():
    with pytest.raises(ValueError):
        Simulation(Parametres(integrateur="inexistant"))


def test_tous_les_integrateurs_enregistres():
    assert set(INTEGRATEURS) == {"Runge-Kutta 4", "Verlet-vitesse", "Euler"}
