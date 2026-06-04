Avyro.requireAuth();

function flash(id, ok, text) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = `text-sm sm:col-span-2 ${ok ? "text-green-600" : "text-red-600"}`;
}

function errText(ex) {
  return (
    ex.data?.message || JSON.stringify(ex.data?.messages || {}) || "Erreur"
  );
}

// ---- Compte utilisateur ----
const userForm = document.getElementById("user-form");

(async () => {
  const me = await Avyro.api("/auth/me");
  userForm.first_name.value = me.first_name;
  userForm.last_name.value = me.last_name;
  userForm.email.value = me.email;
  userForm.phone.value = me.phone || "";

  // Section société réservée aux admins.
  if (me.role !== "admin") {
    document.getElementById("company-section").remove();
    return;
  }
  const company = await Avyro.api("/companies/me");
  const cf = document.getElementById("company-form");
  cf.name.value = company.name;
  cf.kind.value = company.kind;
  cf.siret.value = company.siret || "";
  cf.contact_email.value = company.contact_email || "";
})();

userForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    first_name: userForm.first_name.value,
    last_name: userForm.last_name.value,
    email: userForm.email.value,
    phone: userForm.phone.value,
  };
  if (userForm.password.value) body.password = userForm.password.value;
  try {
    const updated = await Avyro.api("/auth/me", { method: "PATCH", body });
    localStorage.setItem("avyro_user", JSON.stringify(updated));
    userForm.password.value = "";
    flash("user-msg", true, "Profil mis à jour.");
  } catch (ex) {
    flash("user-msg", false, errText(ex));
  }
});

// ---- Société ----
const companyForm = document.getElementById("company-form");
if (companyForm) {
  companyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      name: companyForm.name.value,
      kind: companyForm.kind.value,
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
