/**
 * profile.js — Logique de la page de profil (/profile.html)
 *
 * Deux sections indépendantes :
 *   1. Compte utilisateur  : nom, email, téléphone, mot de passe
 *      → PATCH /api/auth/me
 *   2. Société (admin only): nom, type, SIRET, email de contact
 *      → PATCH /api/companies/me
 *
 * La section "société" est masquée/supprimée du DOM si l'utilisateur
 * n'est pas admin (rôle vérifié depuis GET /api/auth/me).
 */
Avyro.requireAuth();

/**
 * Affiche un message flash sous un formulaire.
 *
 * @param {string}  id  - id de l'élément DOM destinataire
 * @param {boolean} ok  - true → vert (succès), false → rouge (erreur)
 * @param {string}  text - Message à afficher
 */
function flash(id, ok, text) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = `text-sm sm:col-span-2 ${ok ? "text-green-600" : "text-red-600"}`;
}

/**
 * Extrait un message lisible depuis une erreur API.
 * Priorité : message singulier → messages de validation sérialisés → "Erreur".
 */
function errText(ex) {
  return (
    ex.data?.message || JSON.stringify(ex.data?.messages || {}) || "Erreur"
  );
}

// ── Chargement initial ────────────────────────────────────────────────────────

const userForm = document.getElementById("user-form");

(async () => {
  // Pré-remplit le formulaire utilisateur depuis GET /api/auth/me
  const me = await Avyro.api("/auth/me");
  userForm.first_name.value = me.first_name;
  userForm.last_name.value = me.last_name;
  userForm.email.value = me.email;
  userForm.phone.value = me.phone || "";

  // La section société n'est accessible qu'aux admins
  if (me.role !== "admin") {
    document.getElementById("company-section").remove();
    return;
  }
  // Pré-remplit le formulaire société depuis GET /api/companies/me
  const company = await Avyro.api("/companies/me");
  const cf = document.getElementById("company-form");
  cf.name.value = company.name;
  cf.kind.value = company.kind;
  cf.siret.value = company.siret || "";
  cf.contact_email.value = company.contact_email || "";
})();

// ── Sauvegarde du profil utilisateur ─────────────────────────────────────────

userForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    first_name: userForm.first_name.value,
    last_name: userForm.last_name.value,
    email: userForm.email.value,
    phone: userForm.phone.value,
  };
  // Le mot de passe n'est envoyé que s'il est renseigné
  if (userForm.password.value) body.password = userForm.password.value;
  try {
    const updated = await Avyro.api("/auth/me", { method: "PATCH", body });
    // Met à jour le cache local pour que le header affiche le bon nom
    localStorage.setItem("avyro_user", JSON.stringify(updated));
    userForm.password.value = "";
    flash("user-msg", true, "Profil mis à jour.");
  } catch (ex) {
    flash("user-msg", false, errText(ex));
  }
});

// ── Sauvegarde des informations de la société ─────────────────────────────────

const companyForm = document.getElementById("company-form");
if (companyForm) {
  companyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      name: companyForm.name.value,
      kind: companyForm.kind.value,
      // null efface les champs optionnels côté API
      siret: companyForm.siret.value || null,
      contact_email: companyForm.contact_email.value || null,
    };
    try {
      await Avyro.api("/companies/me", { method: "PATCH", body });
      flash("company-msg", true, "Structure mise à jour.");
    } catch (ex) {
      flash("company-msg", false, errText(ex));
    }
  });
}
