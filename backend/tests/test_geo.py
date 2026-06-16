"""Tests de l'utilitaire géographique et du filtre géo du catalogue."""
import math

from app.utils.geo import haversine_km, apply_geo_filter
from tests.conftest import auth_headers_for, create_training


# ── haversine_km ──────────────────────────────────────────────────────────────

def test_haversine_same_point():
    assert haversine_km(48.8566, 2.3522, 48.8566, 2.3522) == 0.0


def test_haversine_paris_lyon():
    """Paris → Lyon : ~392 km à vol d'oiseau."""
    dist = haversine_km(48.8566, 2.3522, 45.7640, 4.8357)
    assert 380 < dist < 410


def test_haversine_paris_bordeaux():
    """Paris → Bordeaux : ~500 km."""
    dist = haversine_km(48.8566, 2.3522, 44.8378, -0.5792)
    assert 490 < dist < 520


def test_haversine_symetric():
    """La distance A→B doit être égale à B→A."""
    d1 = haversine_km(48.8566, 2.3522, 45.7640, 4.8357)
    d2 = haversine_km(45.7640, 4.8357, 48.8566, 2.3522)
    assert math.isclose(d1, d2, rel_tol=1e-9)


def test_haversine_positive():
    """La distance est toujours positive (ou nulle)."""
    dist = haversine_km(0.0, 0.0, 1.0, 1.0)
    assert dist >= 0


# ── apply_geo_filter ──────────────────────────────────────────────────────────

def _item(title, lat=None, lng=None, is_remote=False):
    return {
        "title": title,
        "latitude": lat,
        "longitude": lng,
        "is_remote": is_remote,
        "distance_km": None,
    }


def test_geo_filter_within_radius():
    """Item dans le rayon : inclus avec distance calculée."""
    items = [_item("Proche", lat=48.8566, lng=2.3522)]
    result = apply_geo_filter(items, lat=48.8566, lng=2.3522, radius_km=10)
    assert len(result) == 1
    assert result[0]["distance_km"] == 0.0


def test_geo_filter_excludes_distant():
    """Item hors rayon : exclu."""
    items = [_item("Loin", lat=45.7640, lng=4.8357)]  # Lyon
    result = apply_geo_filter(items, lat=48.8566, lng=2.3522, radius_km=10)
    assert result == []


def test_geo_filter_includes_remote_always():
    """Les offres distancielles sont toujours incluses quel que soit le rayon."""
    items = [_item("Remote", is_remote=True)]
    result = apply_geo_filter(items, lat=48.8566, lng=2.3522, radius_km=1)
    assert len(result) == 1
    assert result[0]["distance_km"] is None


def test_geo_filter_excludes_no_coords():
    """Item physique sans coordonnées : exclu (distance incalculable)."""
    items = [_item("Sans coords", lat=None, lng=None)]
    result = apply_geo_filter(items, lat=48.8566, lng=2.3522, radius_km=1000)
    assert result == []


def test_geo_filter_sorted_by_distance():
    """Les résultats sont triés du plus proche au plus loin."""
    items = [
        _item("Moyen", lat=48.9000, lng=2.3522),
        _item("Proche", lat=48.8600, lng=2.3522),
        _item("Remote", is_remote=True),
    ]
    result = apply_geo_filter(items, lat=48.8566, lng=2.3522, radius_km=100)
    distances = [r["distance_km"] for r in result if r["distance_km"] is not None]
    assert distances == sorted(distances)


def test_geo_filter_remote_distance_is_none():
    """distance_km est None pour les offres distancielles."""
    items = [_item("Remote", is_remote=True)]
    result = apply_geo_filter(items, lat=48.8566, lng=2.3522, radius_km=50)
    assert result[0]["distance_km"] is None


def test_geo_filter_at_radius_boundary():
    """Item exactement à la limite du rayon : inclus (≤)."""
    lat_ref, lng_ref = 48.8566, 2.3522
    # Paris → Lyon ≈ 392 km
    dist_paris_lyon = haversine_km(lat_ref, lng_ref, 45.7640, 4.8357)
    items = [_item("Lyon", lat=45.7640, lng=4.8357)]

    # Rayon légèrement inférieur : exclu
    result_out = apply_geo_filter(items, lat_ref, lng_ref,
                                  radius_km=dist_paris_lyon - 1)
    assert result_out == []

    # Rayon légèrement supérieur : inclus
    result_in = apply_geo_filter(items, lat_ref, lng_ref,
                                 radius_km=dist_paris_lyon + 1)
    assert len(result_in) == 1


# ── Filtre géo via l'API REST ─────────────────────────────────────────────────

def test_api_geo_filter_includes_nearby(client):
    """Via l'API : une formation proche est retournée."""
    prov = auth_headers_for(client, "geo_prov@x.com",
                            company_name="GeoProv", with_siret=True)
    other = auth_headers_for(client, "geo_other@x.com",
                             company_name="GeoOther")

    # Paris
    client.post(
        "/api/trainings", headers=prov,
        json={
            "title": "Formation Paris",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 5,
            "latitude": 48.8566,
            "longitude": 2.3522,
        },
    )

    res = client.get(
        "/api/trainings?lat=48.8566&lng=2.3522&radius=10",
        headers=other,
    )
    results = res.get_json()
    assert any(r["title"] == "Formation Paris" for r in results)
    assert all(r["distance_km"] is not None or r["is_remote"]
               for r in results if r.get("latitude"))


def test_api_geo_filter_excludes_far(client):
    """Via l'API : une formation éloignée est exclue."""
    prov = auth_headers_for(client, "geo2_prov@x.com",
                            company_name="Geo2Prov", with_siret=True)
    other = auth_headers_for(client, "geo2_other@x.com",
                             company_name="Geo2Other")

    # Lyon (~392 km de Paris)
    client.post(
        "/api/trainings", headers=prov,
        json={
            "title": "Formation Lyon",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 5,
            "latitude": 45.7640,
            "longitude": 4.8357,
        },
    )

    res = client.get(
        "/api/trainings?lat=48.8566&lng=2.3522&radius=10",
        headers=other,
    )
    results = res.get_json()
    assert not any(r["title"] == "Formation Lyon" for r in results)
