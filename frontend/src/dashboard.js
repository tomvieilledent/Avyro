Avyro.requireAuth();

const user = Avyro.currentUser();
document.getElementById("who").textContent = user
  ? `${user.full_name}`
  : "";

document.getElementById("logout").addEventListener("click", () => {
  Avyro.clearSession();
  location.href = "login.html";
});

const fmtDate = (s) =>
  new Date(s).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" });

// ---- Mode : Avyro bleu (formations) / Avyro vert (salles de réunion) ----
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
const currentMode =
  localStorage.getItem("avyro_mode") === "room" ? "room" : "training";
const MODE = MODES[currentMode];
const kindQS = `kind=${MODE.kind}`;

// ---- Onglets ----
const tabs = document.querySelectorAll(".tab");
function activate(name) {
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

// ---- Bascule de mode avec fondu (transition fluide) ----
function switchMode(target) {
  if (target === currentMode) return;
  localStorage.setItem("avyro_mode", target);
  document.body.classList.add("page-leave"); // fondu sortant
  setTimeout(() => location.reload(), 180);
}

// ---- Application du mode (libellés, couleurs, contrôle segmenté) ----
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
    const activeText =
      btn.dataset.mode === "room" ? "text-green-700" : "text-avyro-700";
    btn.classList.toggle("bg-white", active);
    btn.classList.toggle(activeText, active);
    btn.classList.toggle("shadow", active);
    btn.classList.toggle("text-white/80", !active);
    btn.onclick = () => switchMode(btn.dataset.mode);
  });
}
applyMode();

// Détermine l'état d'une formation selon les dates et les places.
function trainingState(t) {
  const now = new Date();
  if (now >= new Date(t.ends_at)) return "ended"; // terminée -> supprimée côté serveur
  if (now >= new Date(t.starts_at)) return "running"; // en cours -> vert
  if (t.available_seats <= 0) return "full"; // complète -> jaune
  return "open";
}

const STATE_STYLE = {
  full: {
    card: "border-yellow-300 bg-yellow-50 opacity-90",
    badge: "bg-yellow-100 text-yellow-800",
    label: "Complète",
  },
  running: {
    card: "border-green-300 bg-green-50 opacity-90",
    badge: "bg-green-100 text-green-800",
    label: "En cours",
  },
};

// ---- Rendu cellule formation (ligne uniforme : infos à gauche, action à droite) ----
function trainingCard(t, { canBook, owner } = {}) {
  const state = trainingState(t);
  if (state === "ended") return null; // ne pas afficher une formation terminée

  const el = document.createElement("div");
  el.className =
    "card flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between";

  let action;
  if (owner) {
    if (state !== "open") el.className += ` ${STATE_STYLE[state].card}`;
    action = `<div class="flex shrink-0 gap-2">
        <button class="btn-ghost" data-edit>Éditer</button>
        <button class="btn-ghost text-red-600" data-delete>Supprimer</button>
      </div>`;
  } else if (state === "open") {
    action =
      canBook && t.available_seats > 0
        ? `<div class="shrink-0">
             <button class="btn-primary w-full sm:w-auto" data-book>Réserver</button>
           </div>`
        : `<span class="shrink-0 rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">${t.status}</span>`;
  } else {
    const s = STATE_STYLE[state];
    el.className += ` ${s.card}`;
    action = `<span class="shrink-0 rounded-full ${s.badge} px-3 py-1 text-xs font-medium">${s.label}</span>`;
  }

  el.innerHTML = `
    <div class="min-w-0 flex-1">
      <h3 class="truncate font-semibold">${t.title}</h3>
      <p class="mt-0.5 truncate text-sm text-gray-500">${t.provider_name}</p>
      <p class="mt-2 line-clamp-2 text-sm text-gray-600">${t.description || ""}</p>
      <dl class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-700">
        <div>📅 ${fmtDate(t.starts_at)}</div>
        <div>📍 ${t.is_remote ? "À distance" : t.location || "—"}</div>
        <div>🎟️ <b>${t.available_seats}</b> places · ${t.price_per_seat} €/place</div>
        <div>📞 ${t.contact_phone}</div>
      </dl>
    </div>
    ${action}`;

  const bookBtn = el.querySelector("[data-book]");
  if (bookBtn) bookBtn.onclick = () => book(t);
  const editBtn = el.querySelector("[data-edit]");
  if (editBtn) editBtn.onclick = () => openModal(t);
  const delBtn = el.querySelector("[data-delete]");
  if (delBtn) delBtn.onclick = () => deleteTraining(t);
  return el;
}

async function deleteTraining(t) {
  if (!confirm(MODE.deleteConfirm(t))) return;
  try {
    await Avyro.api(`/trainings/${t.id}`, { method: "DELETE" });
    loaders.mine();
  } catch (e) {
    alert(e.data?.message || "Erreur");
  }
}

async function book(t) {
  const seats = parseInt(prompt(MODE.bookPrompt(t.available_seats), "1"), 10);
  if (!seats) return;
  try {
    await Avyro.api("/bookings", {
      method: "POST",
      body: { training_id: t.id, seats },
    });
    alert("Demande envoyée.");
    loaders.catalog();
  } catch (e) {
    alert(e.data?.message || "Erreur");
  }
}

// ---- Loaders ----
const loaders = {
  async catalog() {
    const q = document.getElementById("search").value;
    const list = await Avyro.api(
      `/trainings?${kindQS}${q ? `&q=${encodeURIComponent(q)}` : ""}`
    );
    const c = document.getElementById("catalog-list");
    c.innerHTML = "";
    list
      .filter((t) => t.provider_id !== user.company_id)
      .forEach((t) => {
        const card = trainingCard(t, { canBook: true });
        if (card) c.appendChild(card);
      });
    if (!c.children.length)
      c.innerHTML = `<p class="text-sm text-gray-500">${MODE.catalogEmpty}</p>`;
  },

  async mine() {
    const list = await Avyro.api(`/trainings?mine=true&${kindQS}`);
    const c = document.getElementById("mine-list");
    c.innerHTML = "";
    list.forEach((t) => {
      const card = trainingCard(t, { owner: true });
      if (card) c.appendChild(card);
    });
    if (!c.children.length)
      c.innerHTML = `<p class="text-sm text-gray-500">${MODE.mineEmpty}</p>`;
  },

  async bookings() {
    const list = await Avyro.api(`/bookings?${kindQS}`);
    const c = document.getElementById("bookings-list");
    c.innerHTML = "";
    list.forEach((b) => {
      const el = document.createElement("div");
      el.className = "card flex items-center justify-between gap-3";
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

  async incoming() {
    const list = await Avyro.api(`/bookings/incoming?${kindQS}`);
    const c = document.getElementById("incoming-list");
    c.innerHTML = "";
    list.forEach((b) => {
      const el = document.createElement("div");
      el.className = "card flex items-center justify-between";
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

  async reports() {
    const list = await Avyro.api(`/trainings/reports?${kindQS}`);
    const c = document.getElementById("reports-list");
    c.innerHTML = "";
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
          <h3 class="font-semibold">${r.training_title}</h3>
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

document.getElementById("search").addEventListener("input", () => {
  clearTimeout(window._t);
  window._t = setTimeout(loaders.catalog, 300);
});

// ---- Modale (création / édition) ----
const modal = document.getElementById("modal");
const form = document.getElementById("training-form");
let editingId = null;

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
    form.location.value = training.location || "";
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

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const err = document.getElementById("training-error");
  err.classList.add("hidden");
  const body = Object.fromEntries(f.entries());
  body.shared_seats = parseInt(body.shared_seats, 10);
  body.price_per_seat = parseFloat(body.price_per_seat || "0");
  body.kind = MODE.kind;
  try {
    if (editingId) {
      await Avyro.api(`/trainings/${editingId}`, { method: "PATCH", body });
    } else {
      await Avyro.api("/trainings", { method: "POST", body });
    }
    closeModal();
    e.target.reset();
    editingId = null;
    activate("mine");
  } catch (ex) {
    err.textContent =
      ex.data?.message || JSON.stringify(ex.data?.messages || {}) || "Erreur";
    err.classList.remove("hidden");
  }
});

activate("catalog");
