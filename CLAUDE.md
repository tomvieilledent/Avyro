# Règles projet Avyro

## Stack autorisée
- **Backend** : Python uniquement
- **Frontend** : React (Vite) + Tailwind CSS
- Pas de CSS pur en dehors des classes Tailwind et de `src/index.css` (pas de `style=""` sauf valeurs dynamiques calculées en JS, ex. filtres/positions SVG)
- Pas d'autres langages backend (Node.js, Ruby, Go, etc.)

## Contraintes d'architecture frontend
- Le frontend est une SPA à page unique (`index.html`), routée côté client par `react-router-dom` (voir `src/App.jsx`). Le backend Flask (`SERVE_FRONTEND`) sert `index.html` en fallback pour toute route non-`/api/*` qui ne correspond pas à un fichier statique du build (voir `_register_frontend` dans `backend/app/__init__.py`).
- L'email d'invitation pointe vers `/invite?token=...` (route client, pas un fichier physique).
- Le client appelle l'API via des chemins relatifs `/api/...` (voir `src/lib/api.js`). En dev, `vite.config.js` relaie `/api` vers le backend Flask sur `:8080` — ne pas coder d'URL absolue.

## Dans la limite du possible
Si une fonctionnalité nécessite absolument une exception (ex : `style="display:none"` pour compatibilité JS), la signaler explicitement.
