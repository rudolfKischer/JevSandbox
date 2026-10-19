import { bare } from './notation.js';

function canon(units) {
  const merged = [];
  for (const unit of units) {
    const sounds = unit.p.map(bare);
    const last = merged[merged.length - 1];
    if (last && !sounds.length && !last.p.length) last.s += unit.s;
    else merged.push({ s: unit.s, p: sounds });
  }
  return merged;
}

function keys(units) {
  let start = 0;
  return canon(units).map(unit => {
    const key = `${start}:${start + unit.s.length}:${unit.p.join('+')}`;
    start += unit.s.length;
    return key;
  });
}

export function signature(units) {
  return keys(units).join('|');
}

export function matches(pred, gold, extra) {
  const wanted = new Set([...keys(gold), ...(extra || []).flatMap(keys)]);
  return keys(pred).map(key => wanted.has(key));
}

export function wordStatus(row, unsureBelow) {
  if (row.judge) return { ok: 'ok', doubtful: 'unsure', unread: 'unsure', wrong: 'no' }[row.judge.verdict];
  if (row.exact === null && row.pred) return (row.posterior ?? 1) < unsureBelow ? 'unsure' : 'na';
  if (row.pick !== undefined) return row.exact ? (row.posterior < unsureBelow ? 'unsure' : 'ok') : 'no';
  if (!row.pred) return 'na';
  if (!row.exact) return 'no';
  return row.posterior !== undefined && row.posterior < unsureBelow ? 'unsure' : 'ok';
}

export function markedUnits(row) {
  const hits = row.gold.length ? matches(row.pred, row.gold, row.accept) : null;
  const merged = [];
  for (const unit of row.pred) {
    const last = merged[merged.length - 1];
    if (last && !unit.p.length && !last.p.length) { last.s += unit.s; last.c = Math.min(last.c ?? 1, unit.c ?? 1); }
    else merged.push({ ...unit });
  }
  return merged.map((unit, index) => ({ ...unit, miss: hits ? !hits[index] : false }));
}
