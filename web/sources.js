import { loadNotation } from './notation.js';
import { esc, laneHtml } from './units.js';
import './tips.js';
import { mountShell } from './shell.js';

const state = { notation: 'plain', source: null, filter: 'all', differs: new Set(), selected: null, pattern: null };
let copy = {};
let data = {};
const $ = id => document.getElementById(id);
const pct = v => Math.round(v * 100) + '%';
const seg = (id, label, tip, on) => `<button class="seg${on ? ' on' : ''}" data-id="${id}" data-tip="${esc(tip)}">${esc(label)}</button>`;
const meta = id => data.sources.find(s => s.id === id);
const reference = () => (data.summary.coverage.ours ? 'ours' : 'ours-free');

function share(a, b) {
  const cell = data.summary.matrix[a]?.[b];
  return cell && cell.n ? { value: cell.structure / cell.n, n: cell.n } : null;
}

function tagsHtml(source) {
  return `<span class="tags" data-tip="${esc(copy.sharesTip)}">${source.shares.map(s => `<span class="chip">${esc(copy.shares[s] || s)}</span>`).join('')}</span>`;
}

function renderRank() {
  const ref = reference();
  const rows = data.sources.filter(s => data.summary.coverage[s.id]).map((s, i) => {
    const agree = s.id === ref ? null : share(ref, s.id);
    const covered = data.summary.coverage[s.id].toLocaleString();
    const bar = agree ? `<span class="rank-bar"><i style="--c:${Math.round(agree.value * 100)}%"></i></span><em data-tip="${agree.n.toLocaleString()} ${esc(copy.board.covers)}">${pct(agree.value)}</em>` : `<span class="rank-bar"></span><em>${esc(copy.board.self)}</em>`;
    return `<button class="rank-row${s.id === state.source ? ' on' : ''}" data-source="${esc(s.id)}"><span class="badge">${'ABCDEFG'[i]}</span><span class="rank-text"><b>${esc(s.label)}</b><small>${covered} ${esc(copy.board.covers)}</small></span>${bar}</button>`;
  }).join('');
  $('rank').innerHTML = `<div class="rank-head"><span class="wide" style="grid-column:1/-1">${esc(copy.board.sources)} · ${esc(copy.board.agree)}</span></div><div class="rank-scroll">${rows}</div>`;
}

function renderHow() {
  const s = meta(state.source);
  const ref = reference();
  const lines = data.sources.filter(o => o.id !== s.id && data.summary.coverage[o.id]).map(o => {
    const v = share(s.id, o.id);
    return v ? `<div class="barrow"><span>${esc(o.label)}</span><span class="track"><i style="--c:${Math.round(v.value * 100)}%"></i></span><b>${pct(v.value)}</b></div>` : '';
  }).join('');
  $('how').innerHTML = `<h2>${esc(s.label)}${s.id === ref ? '' : ''}</h2><p class="how-blurb">${esc(s.note)}</p>${tagsHtml(s)}<div class="how-label">${esc(copy.board.bars)}</div><div class="bars">${lines}</div>`;
}

function renderMatrix() {
  const ids = data.sources.map(s => s.id).filter(id => data.summary.coverage[id]);
  const head = `<tr><th></th>${ids.map(id => `<th>${esc(meta(id).label)}</th>`).join('')}</tr>`;
  const rows = ids.map(a => `<tr><th>${esc(meta(a).label)}</th>${ids.map(b => {
    if (a === b) return '<td class="self">·</td>';
    const v = share(a, b);
    if (!v) return '<td class="self">–</td>';
    const level = Math.round(v.value * 100);
    return `<td class="${level > 55 ? 'dark' : ''}" style="--c:${level}%" data-tip="${v.n.toLocaleString()} ${esc(copy.board.covers)}">${level}%<small>${v.n.toLocaleString()}</small></td>`;
  }).join('')}</tr>`).join('');
  $('matrix-title').textContent = copy.matrixTitle;
  $('matrix-title').dataset.tip = copy.matrixTip;
  $('matrix').innerHTML = `<table class="matrix">${head}${rows}</table>`;
}

function renderHeadline() {
  const s = data.summary;
  const h = copy.headline;
  $('headline').innerHTML = `<span class="big">${pct(s.all_agree / s.compared_words)}</span><span class="sub">${h.agree} · ${s.compared_words.toLocaleString()} ${h.words} · ${s.outvoted.toLocaleString()} ${h.outvoted} · ${s.majority_differ.toLocaleString()} ${h.majority}. ${h.note}</span>`;
}

function renderFilters() {
  const f = copy.filters;
  const segs = ['all', 'outvoted', 'most'].map(id => seg(id, f[id].label, f[id].tip, state.filter === id)).join('');
  const chips = data.sources.filter(s => s.id !== reference() && data.summary.coverage[s.id]).map(s => `<button class="pill tiny${state.differs.has(s.id) ? ' on' : ''}" data-differs="${esc(s.id)}">differs from ${esc(s.label)}</button>`).join('');
  $('filters').innerHTML = `<div class="segs" id="filter-segs">${segs}</div>${chips}`;
}

function renderPatterns() {
  $('patterns-title').textContent = copy.patternsTitle;
  $('patterns-title').dataset.tip = copy.patternsTip;
  $('patterns').innerHTML = (data.summary.patterns || []).slice(0, 28).map((p, i) => `<button class="pill tiny${state.pattern === i ? ' on' : ''}" data-pattern="${i}" data-tip="${esc(p.words.join(', '))}">${esc(p.pattern)} <b>${p.n.toLocaleString()}</b> · ${esc(meta(p.source).label.split(' ')[0])}</button>`).join('');
}

const hasPattern = w => {
  const p = data.summary.patterns[state.pattern];
  return Object.values(w.windows || {}).some(list => list.includes(p.pattern));
};

function visible() {
  return data.words.filter(w => {
    if (state.pattern !== null && !hasPattern(w)) return false;
    if (state.filter === 'outvoted' && !(w.compared >= 2 && w.disagree === w.compared)) return false;
    if (state.filter === 'most' && !(w.disagree * 2 > w.compared)) return false;
    return [...state.differs].every(id => w.relations[id] === 'different');
  });
}

function unitsOf(text, structureOnly) {
  return text.split(' ').map(token => {
    const [s, sounds = ''] = token.split(':');
    const p = sounds === '-' ? [] : sounds.split('+').map(x => (structureOnly && x === '?' ? '·' : x));
    return { s, p };
  });
}

function card(w) {
  const units = unitsOf(w.aligns[w.reference], false).map(u => `<span class="u"><span class="g">${esc(u.s)}</span></span>`).join('');
  const mark = w.disagree ? `<span class="mark no" data-tip="${w.disagree} of ${w.compared}">${w.disagree}/${w.compared}</span>` : '<span class="mark ok">✓</span>';
  return `<button class="card${w.id === state.selected ? ' sel' : ''}" data-word="${esc(w.id)}"><div class="card-head"><span class="card-word">${esc(w.word)}</span>${mark}</div><div class="mini">${units}</div></button>`;
}

function renderPanel() {
  const w = data.words.find(x => x.id === state.selected);
  if (!w) { $('panel').innerHTML = `<div class="empty">${esc(copy.empty)}</div>`; return; }
  const lanes = data.sources.filter(s => w.aligns[s.id]).map(s => {
    const kind = w.relations[s.id];
    const chip = s.id === w.reference ? `<span class="chip">${esc(copy.relation.self)}</span>` : `<span class="chip ${kind === 'different' ? 'differs' : 'agree'}" data-tip="${esc(copy.relation[kind])}">${esc(copy.relationShort[kind])}</span>`;
    const note = s.kind === 'structure' ? `<div class="relrow">${esc(copy.structureOnly)}</div>` : '';
    return laneHtml(s.label, unitsOf(w.aligns[s.id], s.kind === 'structure'), state, copy).replace('</div></div></div>', `</div></div>${chip}${note}</div>`);
  }).join('');
  $('panel').innerHTML = `<div class="p-head"><span class="p-word">${esc(w.word)}</span></div>${lanes}`;
}

function renderAll() {
  $('notation').innerHTML = copy.notations.map(n => seg(n.id, n.label, n.tip, n.id === state.notation)).join('');
  renderRank(); renderHow(); renderMatrix(); renderHeadline(); renderFilters(); renderPatterns();
  $('grid').innerHTML = visible().slice(0, 2000).map(card).join('');
  renderPanel();
}

function onClick(event) {
  const t = event.target.closest('button');
  if (!t) return;
  if (t.dataset.pattern !== undefined) { const i = Number(t.dataset.pattern); state.pattern = state.pattern === i ? null : i; renderPatterns(); $('grid').innerHTML = visible().slice(0, 2000).map(card).join(''); return; }
  if (t.dataset.source) { state.source = t.dataset.source; renderRank(); return renderHow(); }
  if (t.dataset.word) { state.selected = t.dataset.word; $('grid').innerHTML = visible().slice(0, 2000).map(card).join(''); return renderPanel(); }
  if (t.dataset.differs) { state.differs.has(t.dataset.differs) ? state.differs.delete(t.dataset.differs) : state.differs.add(t.dataset.differs); renderFilters(); $('grid').innerHTML = visible().slice(0, 2000).map(card).join(''); return; }
  if (t.closest('#notation')) { state.notation = t.dataset.id; return renderAll(); }
  if (t.closest('#filter-segs')) { state.filter = t.dataset.id; renderFilters(); $('grid').innerHTML = visible().slice(0, 2000).map(card).join(''); }
}

let ready = false;

export async function load() {
  if (ready) return;
  copy = await (await fetch('sources-copy.json')).json();
  await loadNotation();
  data = await (await fetch('../results/sources/sources.json')).json();
  ready = true;
}

export function mount() {
  state.source = state.source || reference();
  $('title').textContent = copy.title;
  $('subtitle').textContent = copy.intro;
  renderAll();
}

export function deactivate() {
  document.removeEventListener('click', onClick);
}

export function activate() {
  deactivate();
  document.addEventListener('click', onClick);
  mountShell({ groups: [], active: null });
}
