/**
 * Libellés et messages spécifiques à chaque mode du dashboard (bimodal) :
 *   - "training" (Avyro bleu) : gestion des formations mutualisées
 *   - "room"     (Avyro gris) : gestion des salles de réunion
 */
export const MODES = {
  training: {
    kind: 'training',
    desc: 'Avyro Training — mutualisez vos formations : proposez vos places restantes à d’autres entreprises.',
    tabs: {
      catalog: 'Catalogue',
      mine: 'Mes formations',
      bookings: 'Mes réservations',
      incoming: 'Demandes reçues',
      reports: 'Comptes rendus',
    },
    catalogEmpty: 'Aucune formation disponible.',
    mineEmpty: 'Aucune formation publiée.',
    newBtn: '+ Nouvelle formation',
    modalNew: 'Nouvelle formation',
    modalEdit: 'Modifier la formation',
    titlePlaceholder: 'Titre',
    seatsLabel: 'Places proposées',
    bookPrompt: (max) => `Combien de places ? (max ${max})`,
    deleteConfirm: (t) => `Supprimer la formation « ${t.title} » ?`,
  },
  room: {
    kind: 'room',
    desc: 'Avyro Room — mutualisez vos salles de réunion : proposez vos salles à des entreprises externes.',
    tabs: {
      catalog: 'Salles dispo',
      mine: 'Mes salles',
      bookings: 'Mes réservations',
      incoming: 'Demandes reçues',
      reports: 'Occupants',
    },
    catalogEmpty: 'Aucune salle disponible.',
    mineEmpty: 'Aucune salle publiée.',
    newBtn: '+ Nouvelle salle',
    modalNew: 'Nouvelle salle de réunion',
    modalEdit: 'Modifier la salle',
    titlePlaceholder: 'Nom de la salle',
    seatsLabel: 'Capacité (places)',
    bookPrompt: (max) => `Combien de places ? (max ${max})`,
    deleteConfirm: (t) => `Supprimer la salle « ${t.title} » ?`,
  },
}

export const TAG_OPTIONS = ['IT', 'management', 'RH', 'sécurité', 'langues', 'commercial', 'finance', 'juridique']
