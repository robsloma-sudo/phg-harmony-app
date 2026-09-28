// Descriptions from classic cocktail specs (public.cocktail_reference), for items that have NO description and whose
// name is exactly a classic (case-insensitive). Per handoff/agents/MENU_DATA_ACCESS.md: the venue's own recipe comes
// first; a classic spec may be used when there is none, labelled "standard"; otherwise flag and ask.
// Rows come from references.sql §8 through phg_designer_query: [{cocktail_name, consensus_spec|spec, garnish}].

const nameKey = s => String(s || '').trim().toLowerCase().replace(/\s+/g, ' ');

// "2 oz blanco tequila; 1 oz lime; 0.75 oz orange liqueur; optional agave" -> "Blanco tequila, lime, orange liqueur, agave"
export function specToDescription(spec, garnish) {
  const parts = String(spec || '').split(/[;\n]+/).map(p => p.trim()
    .replace(/^optional\s+/i, '')
    .replace(/^(?:\d+(?:[.,/]\d+)?\s*(?:oz|ml|cl|dash(?:es)?|barspoons?|tsp|tbsp|parts?|drops?)?\.?\s+)/i, '')
    .replace(/\s*\(.*?\)\s*/g, ' ').trim()).filter(Boolean);
  if (garnish && !parts.some(p => new RegExp(String(garnish).split(/\s+/)[0], 'i').test(p))) parts.push(String(garnish).toLowerCase());
  if (parts.length < 2) return null;
  return parts.map((p, i) => i === 0 ? p.charAt(0).toUpperCase() + p.slice(1) : p.toLowerCase()).join(', ');
}

export function applyStandards(doc, rows) {
  const byName = new Map((rows || []).map(r => [nameKey(r.cocktail_name), r]));
  const changes = [];
  const all = (doc.sections || []).flatMap(s => [...(s.items || []), ...(s.subs || []).flatMap(b => b.items || [])]);
  for (const it of all) {
    if (String(it.desc || '').trim()) continue;                 // never overwrite the venue's words
    const r = byName.get(nameKey(it.name));
    if (!r) continue;
    const d = specToDescription(r.consensus_spec || r.spec, r.garnish);
    if (!d) continue;
    it.desc = d;
    it.meta = { ...(it.meta || {}), description_source: 'standard_spec', standard_spec_of: r.cocktail_name };
    changes.push(`"${it.name}" description written from the classic spec (labelled standard; the venue should confirm their build): ${d}.`);
  }
  return changes;
}
