/** Neutralise l'injection de formules tableur (=, +, -, @, tab, CR). */
export function csvCell(v) {
  const s = String(v ?? '')
  return /^[=+\-@\t\r]/.test(s) ? `'${s}` : s
}

/** Construit le contenu CSV (toutes cellules entre guillemets, neutralisées). */
export function toCsv(rows) {
  return rows.map((row) => row.map((v) => `"${csvCell(v).replace(/"/g, '""')}"`).join(',')).join('\n')
}
