import { esc, laneHtmlRaw } from './units.js';

const cache = new Map();

const unitText = unit => `${unit.s}:${unit.p.length ? unit.p.map(x => x.replace(/\d/g, '')).join('+') : '-'}`;

export const eligible = row => Boolean(row && row.pred && row.pred.length && row.pron && (row.category_pred || row.category || 'word') === 'word');

export function slotHtml(copy) {
  return `<div class="sources-slot"><div class="how-label">${esc(copy.sources.title)} <a class="smalllink" href="sources.html">${esc(copy.sources.all)}</a></div><div id="sources-body" class="note">${esc(copy.sources.loading)}</div></div>`;
}

function unitsOf(text, structureOnly) {
  return text.split(' ').map(token => {
    const [s, sounds = ''] = token.split(':');
    return { s, p: sounds === '-' ? [] : sounds.split('+').map(x => (structureOnly && x === '?' ? '·' : x)) };
  });
}

function chip(item, copy) {
  if (!item.relation) return `<span class="chip" data-tip="${esc(copy.sources.noComparison)}">${esc(copy.sources.notComparable)}</span>`;
  const ok = item.relation !== 'different';
  return `<span class="chip ${ok ? 'agree' : 'differs'}" data-tip="${esc(copy.sources.relationTip[item.relation])}">${esc(copy.sources.relation[item.relation])}</span>`;
}

function laneFor(item, state, copy) {
  const units = unitsOf(item.align, item.kind === 'structure');
  const label = `${esc(item.label)} ${chip(item, copy)}`;
  const diff = item.windows && item.windows.length ? `<div class="relrow">${esc(item.windows.join('  ·  '))}</div>` : '';
  const note = item.kind === 'structure' ? `<div class="relrow">${esc(copy.sources.structureOnly)}</div>` : '';
  return laneHtmlRaw(label, units, state, copy).replace(/<\/div><\/div>$/, `</div>${diff}${note}</div>`);
}

function summary(items, copy) {
  const compared = items.filter(i => i.align && i.relation);
  const agree = compared.filter(i => i.relation !== 'different').length;
  return compared.length ? `<div class="relrow"><b>${agree}</b> ${esc(copy.sources.summaryOne)} <b>${compared.length}</b> ${esc(copy.sources.summaryTail)}</div>` : '';
}

export async function fillSources(row, state, copy) {
  const body = document.getElementById('sources-body');
  const ours = row.pred.map(unitText).join(' ');
  const key = `${row.word}|${row.pron}|${ours}`;
  try {
    if (!cache.has(key)) {
      const reply = await fetch(`/api/sources?word=${encodeURIComponent(row.word)}&pron=${encodeURIComponent(row.pron)}&ours=${encodeURIComponent(ours)}`);
      cache.set(key, await reply.json());
    }
  } catch (error) {
    if (document.getElementById('sources-body')) document.getElementById('sources-body').textContent = copy.sources.failed;
    return;
  }
  const items = cache.get(key);
  const target = document.getElementById('sources-body');
  if (!target || state.selected !== row.id) return;
  const present = items.filter(i => i.align);
  target.className = '';
  target.innerHTML = present.length ? summary(items, copy) + present.map(i => laneFor(i, state, copy)).join('') : `<div class="note">${esc(copy.sources.none)}</div>`;
}
