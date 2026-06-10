/**
 * dashboard.js — Logique principale du tableau de bord (/dashboard.html)
 *
 * Le dashboard est bimodal :
 *   - Mode "training" (Avyro bleu) : gestion des formations mutualisées
 *   - Mode "room"     (Avyro vert) : gestion des salles de réunion
 *
 * Le mode actif est persisté dans localStorage (clé : avyro_mode).
 *
 * Cinq onglets :
 *   1. Catalogue   : formations/salles ouvertes proposées par d'autres Companies
 *   2. Mes offres  : formations/salles publiées par l'utilisateur (CRUD)
 *   3. Réservations: demandes effectuées par la Company de l'utilisateur
 *   4. Demandes    : demandes reçues sur les offres de l'utilisateur
 *   5. Rapports    : liste live des inscrits confirmés par formation
 *
 * API consommée :
 *   GET  /api/trainings         → catalogue
 *   GET  /api/trainings?mine=true → mes offres
 *   POST /api/trainings         → créer
 *   PATCH/DELETE /api/trainings/<id> → modifier / supprimer
 *   GET  /api/trainings/reports → rapports
 *   GET  /api/bookings          → mes réservations
 *   GET  /api/bookings/incoming → demandes reçues
 *   POST /api/bookings          → réserver
 *   PATCH /api/bookings/<id>    → confirmer / refuser
 *   DELETE /api/bookings/<id>   → se désinscrire
 */
// ── Lookup CP → ville + coordonnées (département 2 chiffres en fallback) ──────
const CP_LOOKUP = {
  "92400": { city: "Courbevoie",       lat: 48.8917, lng:  2.2421 },
  "69003": { city: "Lyon",             lat: 45.7576, lng:  4.8324 },
  "69001": { city: "Lyon",             lat: 45.7485, lng:  4.8467 },
  "75": { city: "Paris",               lat: 48.8566, lng:  2.3522 },
  "69": { city: "Lyon",                lat: 45.7640, lng:  4.8357 },
  "13": { city: "Marseille",           lat: 43.2965, lng:  5.3698 },
  "33": { city: "Bordeaux",            lat: 44.8378, lng: -0.5792 },
  "44": { city: "Nantes",              lat: 47.2184, lng: -1.5536 },
  "31": { city: "Toulouse",            lat: 43.6047, lng:  1.4442 },
  "67": { city: "Strasbourg",          lat: 48.5734, lng:  7.7521 },
  "59": { city: "Lille",               lat: 50.6292, lng:  3.0573 },
  "06": { city: "Nice",                lat: 43.7102, lng:  7.2620 },
  "35": { city: "Rennes",              lat: 48.1147, lng: -1.6794 },
  "34": { city: "Montpellier",         lat: 43.6119, lng:  3.8772 },
  "38": { city: "Grenoble",            lat: 45.1885, lng:  5.7245 },
  "21": { city: "Dijon",               lat: 47.3220, lng:  5.0415 },
  "57": { city: "Metz",                lat: 49.1193, lng:  6.1757 },
  "54": { city: "Nancy",               lat: 48.6921, lng:  6.1844 },
  "51": { city: "Reims",               lat: 49.2583, lng:  4.0317 },
  "76": { city: "Rouen",               lat: 49.4432, lng:  1.0993 },
  "63": { city: "Clermont-Ferrand",    lat: 45.7772, lng:  3.0870 },
  "29": { city: "Brest",               lat: 48.3905, lng: -4.4860 },
  "87": { city: "Limoges",             lat: 45.8336, lng:  1.2611 },
  "86": { city: "Poitiers",            lat: 46.5802, lng:  0.3404 },
  "64": { city: "Pau",                 lat: 43.2951, lng: -0.3708 },
  "92": { city: "Hauts-de-Seine",      lat: 48.8737, lng:  2.2531 },
  "93": { city: "Seine-Saint-Denis",   lat: 48.9362, lng:  2.3597 },
  "94": { city: "Val-de-Marne",        lat: 48.7886, lng:  2.4652 },
  "78": { city: "Yvelines",            lat: 48.7967, lng:  1.7819 },
  "91": { city: "Essonne",             lat: 48.6314, lng:  2.3019 },
  "77": { city: "Seine-et-Marne",      lat: 48.6236, lng:  2.9563 },
  "95": { city: "Val-d'Oise",          lat: 49.0339, lng:  2.0815 },
};

function resolvePostalCode(cp) {
  return CP_LOOKUP[cp] || CP_LOOKUP[cp.slice(0, 2)] || null;
}

Avyro.requireAuth();

const user = Avyro.currentUser();
document.getElementById("who").textContent = user
  ? `${user.full_name}`
  : "";

document.getElementById("logout").addEventListener("click", () => {
  Avyro.clearSession();
  location.href = "login.html";
});

/** Formate une date ISO en format français (ex. "1 sept. 2026 à 09:00"). */
const fmtDate = (s) =>
  new Date(s).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" });

// ── Configuration des deux modes ──────────────────────────────────────────────

/**
 * MODES : libellés et messages spécifiques à chaque mode d'affichage.
 * Utilisés pour adapter dynamiquement les labels, titres et messages
 * sans dupliquer la logique HTML/JS.
 */
const MODES = {
  training: {
    kind: "training",
    desc: "Avyro Training — mutualisez vos formations : proposez vos places restantes à d'autres entreprises.",
    tabs: {
      catalog: "Catalogue",
      mine: "Mes formations",
      bookings: "Mes réservations",
      incoming: "Demandes reçues",
      reports: "Comptes rendus",
    },
    catalogEmpty: "Aucune formation disponible.",
    mineEmpty: "Aucune formation publiée.",
    newBtn: "+ Nouvelle formation",
    modalNew: "Nouvelle formation",
    modalEdit: "Modifier la formation",
    titlePlaceholder: "Titre",
    seatsLabel: "Places proposées",
    bookPrompt: (max) => `Combien de places ? (max ${max})`,
    deleteConfirm: (t) => `Supprimer la formation « ${t.title} » ?`,
  },
  room: {
    kind: "room",
    desc: "Avyro Room — mutualisez vos salles de réunion : proposez vos salles à des entreprises externes.",
    tabs: {
      catalog: "Salles dispo",
      mine: "Mes salles",
      bookings: "Mes réservations",
      incoming: "Demandes reçues",
      reports: "Occupants",
    },
    catalogEmpty: "Aucune salle disponible.",
    mineEmpty: "Aucune salle publiée.",
    newBtn: "+ Nouvelle salle",
    modalNew: "Nouvelle salle de réunion",
    modalEdit: "Modifier la salle",
    titlePlaceholder: "Nom de la salle",
    seatsLabel: "Capacité (places)",
    bookPrompt: (max) => `Combien de places ? (max ${max})`,
    deleteConfirm: (t) => `Supprimer la salle « ${t.title} » ?`,
  },
};
let currentMode =
  localStorage.getItem("avyro_mode") === "room" ? "room" : "training";
let MODE = MODES[currentMode];
let kindQS = `kind=${MODE.kind}`;

/** Préfixe API selon le mode actif : /rooms ou /trainings. */
const apiBase = () => currentMode === "room" ? "/rooms" : "/trainings";

// ── État géolocalisation ──────────────────────────────────────────────────────
let geoState = { active: false, lat: null, lng: null };

function requestGeo() {
  if (!navigator.geolocation) {
    showToast("Géolocalisation non supportée par ce navigateur.", "error");
    return;
  }
  const btn = document.getElementById("geo-btn");
  btn.textContent = "Localisation…";
  btn.disabled = true;
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      geoState = { active: true, lat: pos.coords.latitude, lng: pos.coords.longitude };
      btn.disabled = false;
      _updateGeoUI();
      loaders.catalog();
    },
    () => {
      btn.disabled = false;
      _updateGeoUI();
      showToast("Impossible d'obtenir votre position. Vérifiez les permissions.", "error");
    },
    { enableHighAccuracy: false, timeout: 8000 }
  );
}

function resetGeo() {
  geoState = { active: false, lat: null, lng: null };
  _updateGeoUI();
  loaders.catalog();
}

function _updateGeoUI() {
  const btn    = document.getElementById("geo-btn");
  const status = document.getElementById("geo-status");
  const stTxt  = document.getElementById("geo-status-text");
  const radius = document.getElementById("geo-radius")?.value || "25";
  if (geoState.active) {
    btn.innerHTML = `<svg fill="currentColor" viewBox="0 0 24 24" style="width:14px;height:14px;flex-shrink:0"><circle cx="12" cy="12" r="3"/><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/></svg> Position active`;
    btn.classList.add("active");
    if (status) status.style.display = "flex";
    if (stTxt)  stTxt.textContent = `Résultats dans un rayon de ${radius} km autour de vous.`;
  } else {
    btn.innerHTML = `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="width:14px;height:14px;flex-shrink:0"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/><circle cx="12" cy="12" r="8" stroke-dasharray="2 2"/></svg> Autour de moi`;
    btn.classList.remove("active");
    if (status) status.style.display = "none";
  }
}

// ── Navigation par onglets ────────────────────────────────────────────────────

const tabs = document.querySelectorAll(".tab");
let activeTab = "catalog";

function activate(name) {
  activeTab = name;
  tabs.forEach((t) =>
    t.classList.toggle("border-b-2", t.dataset.tab === name)
  );
  tabs.forEach((t) =>
    t.classList.toggle("text-avyro-600", t.dataset.tab === name)
  );
  document.querySelectorAll("[data-panel]").forEach((p) =>
    p.classList.toggle("hidden", p.dataset.panel !== name)
  );
  loaders[name]?.();
}
tabs.forEach((t) => t.addEventListener("click", () => activate(t.dataset.tab)));

// ── Bascule de mode (training ↔ room) ────────────────────────────────────────

/**
 * Bascule vers l'autre mode et recharge la page après un fondu sortant.
 * Le mode est persisté dans localStorage pour survivre au rechargement.
 */
function switchMode(target) {
  if (target === currentMode) return;
  currentMode = target;
  MODE = MODES[currentMode];
  kindQS = `kind=${MODE.kind}`;
  localStorage.setItem("avyro_mode", target);
  applyMode();
  activate(activeTab);
}

/**
 * Applique les libellés, couleurs et états du contrôle segmenté au DOM
 * en fonction du mode actif.
 */
function applyMode() {
  const isRoom = currentMode === "room";
  document.body.classList.toggle("mode-room", isRoom);
  const mark = isRoom ? "assets/mark-room.svg" : "assets/mark-training.svg";
  document.getElementById("brand-mark").src = mark;
  document.getElementById("favicon").href = mark;
  document.getElementById("mode-desc").textContent = MODE.desc;
  document.getElementById("new-training").textContent = MODE.newBtn;
  tabs.forEach((t) => {
    if (MODE.tabs[t.dataset.tab]) t.textContent = MODE.tabs[t.dataset.tab];
  });

  document.querySelectorAll(".mode-seg").forEach((btn) => {
    const active = btn.dataset.mode === currentMode;
    const activeText = "text-avyro-700";
    btn.classList.toggle("bg-white", active);
    btn.classList.toggle(activeText, active);
    btn.classList.toggle("shadow", active);
    btn.classList.toggle("text-white/80", !active);
    btn.onclick = () => switchMode(btn.dataset.mode);
  });
}
applyMode();

// ── Calcul de l'état d'une Training ──────────────────────────────────────────

/**
 * Détermine l'état visuel d'une formation à partir de ses données.
 *
 * États possibles :
 *   "ended"   — date de fin dépassée (ne doit plus être affiché)
 *   "running" — en cours (date de début dépassée mais pas la fin)
 *   "full"    — complet (0 place disponible)
 *   "open"    — normal, places disponibles
 */
function trainingState(t) {
  const now = new Date();
  if (now >= new Date(t.ends_at)) return "ended";
  if (now >= new Date(t.starts_at)) return "running";
  if (t.available_seats <= 0) return "full";
  return "open";
}

/** Styles CSS par état pour les badges et cartes. */
const STATE_STYLE = {
  full: {
    card: "border-yellow-300 bg-yellow-50 opacity-90",
    badge: "bg-yellow-100 text-yellow-800",
    label: "Complète",
  },
  running: {
    card: "border-blue-200 bg-blue-50 opacity-90",
    badge: "bg-blue-100 text-blue-800",
    label: "En cours",
  },
};

// ── Rendu d'une carte Formation / Salle ──────────────────────────────────────

/**
 * Crée et retourne un élément DOM représentant une formation ou une salle.
 *
 * @param {object}  t        - Données de la Training (réponse API)
 * @param {boolean} canBook  - true si l'onglet Catalogue (bouton Réserver visible)
 * @param {boolean} owner    - true si c'est la propre formation de l'utilisateur
 * @returns {HTMLElement|null} - null si la formation est terminée (ne pas l'afficher)
 */
function trainingCard(t, { canBook, owner } = {}) {
  const state = trainingState(t);
  if (state === "ended") return null;

  const el = document.createElement("div");
  el.className =
    "card flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between";

  let action;
  if (owner) {
    // Onglet "Mes offres" : boutons Éditer / Supprimer
    if (state !== "open") el.className += ` ${STATE_STYLE[state].card}`;
    action = `<div class="flex shrink-0 gap-2">
        <button class="btn-ghost" data-edit>Éditer</button>
        <button class="btn-ghost text-red-600" data-delete>Supprimer</button>
      </div>`;
  } else if (state === "open") {
    // Onglet "Catalogue" : bouton Réserver si places disponibles
    action =
      canBook && t.available_seats > 0
        ? `<div class="shrink-0">
             <button class="btn-primary w-full sm:w-auto" data-book>Réserver</button>
           </div>`
        : `<span class="shrink-0 rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">${t.status}</span>`;
  } else {
    // Formation complète ou en cours : badge coloré
    const s = STATE_STYLE[state];
    el.className += ` ${s.card}`;
    action = `<span class="shrink-0 rounded-full ${s.badge} px-3 py-1 text-xs font-medium">${s.label}</span>`;
  }

  const distBadge = t.distance_km != null
    ? `<span class="dist-badge">📍 ${t.distance_km} km</span>`
    : "";
  el.innerHTML = `
    <div class="min-w-0 flex-1">
      <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
        <h3 class="truncate font-semibold">${t.title}</h3>
        ${distBadge}
      </div>
      <p class="mt-0.5 truncate text-sm text-gray-500">${t.provider_name}</p>
      <p class="mt-2 line-clamp-2 text-sm text-gray-600">${t.description || ""}</p>
      <dl class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-700">
        <div><span class="text-gray-400 font-medium">Date</span> · ${fmtDate(t.starts_at)}</div>
        <div><span class="text-gray-400 font-medium">Lieu</span> · ${t.is_remote ? "À distance" : t.location || "—"}</div>
        <div><span class="text-gray-400 font-medium">Places</span> · <b>${t.available_seats}</b> disponibles · ${t.price_per_seat} €/place</div>
        <div><span class="text-gray-400 font-medium">Contact</span> · ${t.contact_phone}</div>
      </dl>
    </div>
    ${action}`;

  // Liaison des handlers sur les boutons d'action
  const bookBtn = el.querySelector("[data-book]");
  if (bookBtn) bookBtn.onclick = () => book(t);
  const editBtn = el.querySelector("[data-edit]");
  if (editBtn) editBtn.onclick = () => openModal(t);
  const delBtn = el.querySelector("[data-delete]");
  if (delBtn) delBtn.onclick = () => deleteTraining(t);
  return el;
}

// ── Actions utilisateur ───────────────────────────────────────────────────────

/** Supprime une formation/salle après confirmation. */
async function deleteTraining(t) {
  if (!confirm(MODE.deleteConfirm(t))) return;
  try {
    await Avyro.api(`${apiBase()}/${t.id}`, { method: "DELETE" });
    loaders.mine();
  } catch (e) {
    alert(e.data?.message || "Erreur");
  }
}

/** Crée une demande de réservation (POST /api/bookings). */
async function book(t) {
  const seats = await promptSeats(t);
  if (!seats) return;
  try {
    const bookBody = currentMode === "room"
      ? { room_id: t.id, seats }
      : { training_id: t.id, seats };
    await Avyro.api("/bookings", { method: "POST", body: bookBody });
    showToast("Demande envoyée avec succès.");
    loaders.catalog();
  } catch (e) {
    showToast(e.data?.message || "Erreur lors de la réservation.", "error");
  }
}

/** Ouvre la modale de saisie du nombre de places, retourne Promise<number|null>. */
function promptSeats(t) {
  return new Promise((resolve) => {
    const overlay  = document.getElementById("book-modal");
    const titleEl  = document.getElementById("book-modal-title");
    const descEl   = document.getElementById("book-modal-desc");
    const input    = document.getElementById("book-seats-input");
    const form     = document.getElementById("book-modal-form");
    const cancelBtn = document.getElementById("book-modal-cancel");

    titleEl.textContent = t.title;
    descEl.textContent  = MODE.bookPrompt(t.available_seats);
    input.value = "1";
    input.max   = String(t.available_seats);
    overlay.classList.replace("hidden", "flex");
    setTimeout(() => input.focus(), 50);

    function cleanup() {
      overlay.classList.replace("flex", "hidden");
      form.removeEventListener("submit", onSubmit);
      cancelBtn.removeEventListener("click", onCancel);
      overlay.removeEventListener("click", onOverlay);
      document.removeEventListener("keydown", onKey);
    }
    function onSubmit(e) {
      e.preventDefault();
      const v = parseInt(input.value, 10);
      cleanup();
      resolve(v > 0 ? v : null);
    }
    function onCancel()  { cleanup(); resolve(null); }
    function onOverlay(e) { if (e.target === overlay) onCancel(); }
    function onKey(e)    { if (e.key === "Escape") onCancel(); }

    form.addEventListener("submit", onSubmit);
    cancelBtn.addEventListener("click", onCancel);
    overlay.addEventListener("click", onOverlay);
    document.addEventListener("keydown", onKey);
  });
}

/** Affiche un toast de notification temporaire (3,5 s). */
function showToast(msg, type) {
  const el    = document.getElementById("toast");
  const msgEl = document.getElementById("toast-msg");
  if (!el || !msgEl) return;
  msgEl.textContent = msg;
  el.className = type === "error" ? "toast-error" : "toast-success";
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.className = "toast-hidden"; }, 3500);
}

// ── Loaders (rechargement des onglets depuis l'API) ───────────────────────────

/**
 * Chaque loader correspond à un onglet du dashboard.
 * Appelés par activate() lors du changement d'onglet, ou directement
 * après une action (création, confirmation, etc.) pour rafraîchir la vue.
 */
const loaders = {
  /** Onglet 1 : Catalogue — formations/salles ouvertes des autres Companies. */
  async catalog() {
    const c = document.getElementById("catalog-list");
    c.innerHTML = "";
    const q      = document.getElementById("search").value;
    const radius = document.getElementById("geo-radius")?.value || "25";
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (geoState.active && geoState.lat != null) {
      params.set("lat", String(geoState.lat));
      params.set("lng", String(geoState.lng));
      params.set("radius", radius);
    }
    const qs   = params.toString();
    const list = await Avyro.api(`${apiBase()}${qs ? "?" + qs : ""}`);
    // Exclut les formations de la propre Company de l'utilisateur
    list
      .filter((t) => t.provider_id !== user.company_id)
      .forEach((t) => {
        const card = trainingCard(t, { canBook: true });
        if (card) c.appendChild(card);
      });
    if (!c.children.length)
      c.innerHTML = `<p class="text-sm text-gray-500">${MODE.catalogEmpty}</p>`;
  },

  /** Onglet 2 : Mes offres — formations/salles publiées par l'utilisateur. */
  async mine() {
    const c = document.getElementById("mine-list");
    c.innerHTML = "";
    const list = await Avyro.api(`${apiBase()}?mine=true`);
    list.forEach((t) => {
      const card = trainingCard(t, { owner: true });
      if (card) c.appendChild(card);
    });
    if (!c.children.length)
      c.innerHTML = `<p class="text-sm text-gray-500">${MODE.mineEmpty}</p>`;
  },

  /** Onglet 3 : Mes réservations — demandes de la Company de l'utilisateur. */
  async bookings() {
    const c = document.getElementById("bookings-list");
    c.innerHTML = "";
    const list = await Avyro.api(`/bookings?${kindQS}`);
    list.forEach((b) => {
      const el = document.createElement("div");
      el.className = "card flex items-center justify-between gap-3";
      // Bouton "Se désinscrire" uniquement si la réservation est encore pending
      const action =
        b.status === "pending"
          ? `<button class="btn-ghost shrink-0 text-red-600" data-unsub>Se désinscrire</button>`
          : "";
      el.innerHTML = `<div class="min-w-0"><b>${b.training_title}</b> — ${b.seats} place(s)
        <span class="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs">${b.status}</span></div>${action}`;
      const btn = el.querySelector("[data-unsub]");
      if (btn)
        btn.onclick = async () => {
          if (!confirm("Se désinscrire de cette formation ?")) return;
          try {
            await Avyro.api(`/bookings/${b.id}`, { method: "DELETE" });
            loaders.bookings();
          } catch (e) {
            alert(e.data?.message || "Erreur");
          }
        };
      c.appendChild(el);
    });
    if (!c.children.length)
      c.innerHTML = '<p class="text-sm text-gray-500">Aucune réservation.</p>';
  },

  /** Onglet 4 : Demandes reçues — réservations à confirmer ou refuser. */
  async incoming() {
    const c = document.getElementById("incoming-list");
    c.innerHTML = "";
    const list = await Avyro.api(`/bookings/incoming?${kindQS}`);
    list.forEach((b) => {
      const el = document.createElement("div");
      el.className = "card flex items-center justify-between";
      // Boutons d'action uniquement sur les demandes encore pending
      const actions =
        b.status === "pending"
          ? `<div class="flex gap-2">
               <button class="btn-primary" data-id="${b.id}" data-s="confirmed">Confirmer</button>
               <button class="btn-ghost" data-id="${b.id}" data-s="cancelled">Refuser</button>
             </div>`
          : `<span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs">${b.status}</span>`;
      el.innerHTML = `<div><b>${b.company_name}</b> · ${b.training_title} — ${b.seats} place(s)</div>${actions}`;
      c.appendChild(el);
    });
    // Délégation d'événements sur les boutons Confirmer / Refuser
    c.querySelectorAll("button[data-id]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        try {
          await Avyro.api(`/bookings/${btn.dataset.id}`, {
            method: "PATCH",
            body: { status: btn.dataset.s },
          });
          loaders.incoming();
        } catch (e) {
          alert(e.data?.message || "Erreur");
        }
      })
    );
    if (!c.children.length)
      c.innerHTML = '<p class="text-sm text-gray-500">Aucune demande.</p>';
  },

  /** Onglet 5 : Rapports — liste live des inscrits confirmés par formation. */
  async reports() {
    const c = document.getElementById("reports-list");
    c.innerHTML = "";
    const list = await Avyro.api(`${apiBase()}/reports`);
    list.forEach((r) => {
      const rows = (r.attendees || [])
        .map(
          (a) => `<tr class="border-t">
              <td class="py-1 pr-4">${a.company_name}</td>
              <td class="py-1 pr-4">${a.seats}</td>
              <td class="py-1 pr-4">${a.contact_name}</td>
              <td class="py-1">${a.contact_email}</td>
            </tr>`
        )
        .join("");
      const el = document.createElement("div");
      el.className = "card";
      el.innerHTML = `
        <div class="flex flex-wrap items-baseline justify-between gap-2">
          <h3 class="font-semibold">${r.training_title || r.room_title}</h3>
          <span class="text-sm text-gray-500">Début : ${fmtDate(r.starts_at)}</span>
        </div>
        <p class="mt-1 text-sm text-gray-600"><b>${r.total_seats}</b> inscrit(s) confirmé(s)</p>
        ${
          rows
            ? `<div class="mt-3 overflow-x-auto"><table class="w-full text-left text-sm">
                 <thead class="text-gray-500"><tr>
                   <th class="pb-1 pr-4 font-medium">Structure</th>
                   <th class="pb-1 pr-4 font-medium">Places</th>
                   <th class="pb-1 pr-4 font-medium">Contact</th>
                   <th class="pb-1 font-medium">Email</th>
                 </tr></thead><tbody>${rows}</tbody></table></div>`
            : '<p class="mt-2 text-sm text-gray-500">Aucun inscrit confirmé.</p>'
        }`;
      c.appendChild(el);
    });
    if (!c.children.length)
      c.innerHTML =
        '<p class="text-sm text-gray-500">Aucun compte rendu pour le moment.</p>';
  },
};

// ── Recherche dans le catalogue ───────────────────────────────────────────────

/** Debounce de 300 ms sur la saisie dans le champ de recherche. */
document.getElementById("search").addEventListener("input", () => {
  clearTimeout(window._t);
  window._t = setTimeout(loaders.catalog, 300);
});

/** Recharge le catalogue quand le rayon change (si géo active). */
document.getElementById("geo-radius")?.addEventListener("change", () => {
  _updateGeoUI();
  if (geoState.active) loaders.catalog();
});

// ── Modale de création / édition ──────────────────────────────────────────────

const modal = document.getElementById("modal");
const form = document.getElementById("training-form");
let editingId = null; // null = création, number = édition

/**
 * Ouvre la modale en mode création (training=null) ou édition (training=objet).
 * Pré-remplit les champs en mode édition.
 */
function openModal(training) {
  const isEdit = training && training.id;
  editingId = isEdit ? training.id : null;
  document.getElementById("modal-title").textContent = isEdit
    ? MODE.modalEdit
    : MODE.modalNew;
  document.getElementById("training-submit").textContent = isEdit
    ? "Enregistrer"
    : "Créer";
  document.getElementById("f-title").placeholder = MODE.titlePlaceholder;
  document.getElementById("f-seats-label").firstChild.nodeValue = MODE.seatsLabel;
  document.getElementById("training-error").classList.add("hidden");
  form.reset();
  if (isEdit) {
    form.title.value = training.title;
    form.description.value = training.description || "";
    const cpMatch = (!training.is_remote && training.location || "").match(/^(\d{5})/);
    form.postal_code.value = cpMatch ? cpMatch[1] : "";
    form.contact_phone.value = training.contact_phone || "";
    form.starts_at.value = training.starts_at.slice(0, 16);
    form.ends_at.value = training.ends_at.slice(0, 16);
    form.shared_seats.value = training.shared_seats;
    form.price_per_seat.value = training.price_per_seat;
  }
  modal.classList.replace("hidden", "flex");
}
const closeModal = () => modal.classList.replace("flex", "hidden");
document.getElementById("new-training").addEventListener("click", () => openModal());
document.getElementById("modal-cancel").addEventListener("click", closeModal);

/** Soumission du formulaire : crée ou met à jour la formation via l'API. */
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const err = document.getElementById("training-error");
  err.classList.add("hidden");
  const body = Object.fromEntries(f.entries());
  body.shared_seats = parseInt(body.shared_seats, 10);
  body.price_per_seat = parseFloat(body.price_per_seat || "0");
  body.kind = MODE.kind;
  delete body.kind;

  // Résolution CP → localisation + coordonnées
  const cp = (body.postal_code || "").trim();
  delete body.postal_code;
  if (!cp) {
    body.is_remote = true;
    body.location = "À distance";
    body.latitude = null;
    body.longitude = null;
  } else {
    const geo = resolvePostalCode(cp);
    body.is_remote = false;
    body.location = geo ? `${cp} ${geo.city}` : cp;
    body.latitude = geo ? geo.lat : null;
    body.longitude = geo ? geo.lng : null;
  }
  try {
    if (editingId) {
      await Avyro.api(`${apiBase()}/${editingId}`, { method: "PATCH", body });
    } else {
      await Avyro.api(apiBase(), { method: "POST", body });
    }
    closeModal();
    e.target.reset();
    editingId = null;
    activate("mine");
  } catch (ex) {
    // Affiche le message d'erreur dans la modale sans la fermer
    err.textContent =
      ex.data?.message || JSON.stringify(ex.data?.messages || {}) || "Erreur";
    err.classList.remove("hidden");
  }
});

// ── Initialisation ────────────────────────────────────────────────────────────

/** Charge le catalogue au démarrage (onglet par défaut). */
activate("catalog");
