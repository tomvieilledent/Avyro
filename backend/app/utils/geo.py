"""Calcul de distance géographique (formule de Haversine)."""
import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Retourne la distance en km entre deux points GPS (great-circle)."""
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def apply_geo_filter(
    items: list[dict],
    lat: float,
    lng: float,
    radius_km: float,
) -> list[dict]:
    """
    Filtre et trie une liste de dicts par distance.

    - Items distants (is_remote=True) : toujours inclus, distance_km=None.
    - Items avec coordonnées : inclus si dans le rayon, distance_km renseigné.
    - Items physiques sans coordonnées : inclus, distance_km=None.
    """
    result = []
    for item in items:
        item["distance_km"] = None
        if item.get("is_remote"):
            result.append(item)
            continue
        item_lat = item.get("latitude")
        item_lng = item.get("longitude")
        if item_lat is None or item_lng is None:
            # Pas de coordonnées : impossible de calculer la distance, on exclut
            continue
        dist = haversine_km(lat, lng, item_lat, item_lng)
        if dist > radius_km:
            continue
        item["distance_km"] = round(dist, 1)
        result.append(item)

    result.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"] or 0))
    return result
