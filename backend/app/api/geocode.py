"""
Proxy de géocodage (Nominatim / OpenStreetMap).
Préfixe : /api/geocode
"""
import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import Schema, fields, validate

from app.extensions import limiter

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "Avyro/1.0"
TIMEOUT_SECONDS = 5

blp = Blueprint(
    "geocode",
    __name__,
    url_prefix="/api/geocode",
    description="Géocodage d'adresses (proxy Nominatim).",
)


class GeocodeQuerySchema(Schema):
    q = fields.Str(required=True, validate=validate.Length(min=3, max=200))


class GeocodeResultSchema(Schema):
    label = fields.Str()
    lat = fields.Float()
    lng = fields.Float()
    line1 = fields.Str()
    postal_code = fields.Str()
    city = fields.Str()


def _to_result(r: dict) -> dict:
    addr = r.get("address") or {}
    if not isinstance(addr, dict):
        addr = {}
    road = str(addr.get("road") or "").strip()
    number = str(addr.get("house_number") or "").strip()
    city = ""
    for key in ("city", "town", "village", "municipality"):
        if addr.get(key):
            city = str(addr[key])
            break
    return {
        "label": str(r["display_name"]),
        "lat": float(r["lat"]),
        "lng": float(r["lon"]),
        "line1": f"{number} {road}".strip() if road else "",
        "postal_code": str(addr.get("postcode") or ""),
        "city": city,
    }


def _search(q: str) -> list:
    params = urlencode({"q": q, "format": "json", "addressdetails": 1, "limit": 5})
    req = Request(
        f"{NOMINATIM_URL}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:  # noqa: S310 (URL fixe https)
        raw = json.loads(resp.read().decode("utf-8"))
    if not isinstance(raw, list):
        raise ValueError("réponse inattendue")
    return [_to_result(r) for r in raw]


@blp.route("")
class GeocodeView(MethodView):
    decorators = [limiter.limit("30 per minute")]

    @blp.doc(security=[])
    @blp.arguments(GeocodeQuerySchema, location="query")
    @blp.response(200, GeocodeResultSchema(many=True))
    @blp.alt_response(502, description="Service de géocodage indisponible.")
    def get(self, args: dict):
        """Recherche d'adresses (max 5 résultats)."""
        try:
            return _search(args["q"])
        except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError):
            logger.exception("Échec du géocodage Nominatim")
            abort(502, message="Service de géocodage indisponible.")
