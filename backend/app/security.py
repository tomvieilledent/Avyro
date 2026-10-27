"""En-têtes de sécurité HTTP, ProxyFix et garde-fous de configuration."""
import logging

from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

logger = logging.getLogger(__name__)

# SPA servie par Flask : tout est auto-hébergé (scripts, styles, polices).
# style-src-attr 'unsafe-inline' : valeurs dynamiques calculées en JS (CLAUDE.md).
_CSP_SPA = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "style-src-attr 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)
# Réponses JSON de l'API : rien n'a vocation à être chargé.
_CSP_API = "default-src 'none'; frame-ancestors 'none'"
# Swagger UI (dev uniquement) : assets du CDN configuré + script inline.
_CSP_DOCS = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
)
_HSTS = "max-age=31536000; includeSubDomains"


def _csp_for(path: str) -> str:
    if path.startswith("/api/docs"):
        return _CSP_DOCS
    if path.startswith("/api/"):
        return _CSP_API
    return _CSP_SPA


def init_security(app: Flask) -> None:
    """Branche ProxyFix, les en-têtes de sécurité et les avertissements prod."""
    hops = int(app.config.get("TRUSTED_PROXY_COUNT", 0) or 0)
    if hops > 0:
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=hops, x_proto=hops, x_host=hops
        )

    is_prod = app.config.get("APP_ENV") == "production"
    if is_prod:
        if str(app.config.get("RATELIMIT_STORAGE_URI", "")).startswith("memory://"):
            logger.warning(
                "RATELIMIT_STORAGE_URI=memory:// en production : les limites ne "
                "sont pas partagées entre workers. Utilisez Redis/Memcached."
            )
        if hops == 0:
            logger.warning(
                "TRUSTED_PROXY_COUNT=0 en production : derrière un reverse proxy, "
                "le rate-limit verra l'IP du proxy. Définissez le nombre de proxys."
            )

    @app.after_request
    def _security_headers(resp):
        h = resp.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "geolocation=(self), camera=(), microphone=()")
        h.setdefault("Content-Security-Policy", _csp_for(request.path))
        if is_prod:
            h.setdefault("Strict-Transport-Security", _HSTS)
        return resp
