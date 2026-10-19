import { loadNotation } from './notation.js';
import { esc } from './units.js';
import { phoneRow, lcsMask, candidateRows } from './pron-view.js';
import './tips.js';
import { mountShell } from './shell.js';

const KEY = 'pron-lab';
const state = { notation: 'plain', set: null, run: null, method: null, sort: 'best', filter: 'all', tags: new Set(), selected: null, detailsOpen: false, tagsOpen: false };
let copy = {};
let runs = [];
let all = {};
let data = null;
const $ = id => document.getElementById(id);
const seg = (id, label, tip, on) => `<button class="seg${on ? ' on' : ''}" data-id="${id}" data-tip="${esc(tip)}">${esc(label)}</button>`;

function remember() { try { localStorage.setItem(KEY, JSON.stringify({ notation: state.notation })); } catch (e) {} }
function restore(useParams = true) {
  try { Object.assign(state, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) {}
  if (!useParams) return;
  const params = new URLSearchParams(location.search);
  if (params.get('run')) state.run = params.get('run');
  if (params.get('method')) state.method = params.get('method');
}

const inSet = () => runs.filter(run => run.set === state.set);
const money = v => (v < 0.01 ? '$' + v.toFixed(4) : '$' + v.toFixed(3));
const fmtTime = v => (v < 0.01 ? (v * 1000).toFixed(1) + ' ms' : v.toFixed(2) + ' s');

function costCell(run, ref) {
  const v = run.summary.per_thousand;
  if (!v) return `<span class="stat"><b>${esc(copy.board.free)}</b></span>`;
  const times = ref ? v / ref : 1;
  return `<span class="stat" data-tip="${money(v)} per 1,000 words, ${times.toFixed(1)}× the cheapest paid method"><b>${money(v)}</b><small>×${times.toFixed(1)}</small></span>`;
}

function timeCell(run, ref) {
  const v = run.summary.seconds_per_word;
  const times = ref && v > ref ? ` <small>×${(v / ref).toFixed(0)}</small>` : '';
  return `<span class="stat" data-tip="${fmtTime(v)} per word"><b>${fmtTime(v)}</b>${times}</span>`;
}

function rankRow(method, run, refs) {
  const info = copy.methods[method];
  const on = method === state.method ? ' on' : '';
  const badge = 'ABCDEFGHIJ'[copy.order.indexOf(method)];
  if (!run) return `<button class="rank-row absent${on}" data-method="${method}"><span class="badge">${esc(badge)}</span><span class="rank-text"><b>${esc(info.name)}</b><small>${esc(info.blurb)}</small></span><span class="notrun">${esc(copy.board.notRun)}</span></button>`;
  const pct = Math.round(run.summary.exact_rate * 100);
  return `<button class="rank-row${on}" data-method="${method}"><span class="badge">${esc(badge)}</span><span class="rank-text"><b>${esc(info.name)}</b><small>${esc(info.blurb)}</small></span>${costCell(run, refs.cost)}${timeCell(run, refs.time)}<span class="rank-bar"><i style="--c:${pct}%"></i></span><em>${pct}%</em></button>`;
}

function renderRank() {
  const here = inSet();
  const byMethod = Object.fromEntries(here.map(run => [run.method, run]));
  const paid = here.map(r => r.summary.per_thousand).filter(v => v > 0);
  const timed = here.map(r => r.summary.seconds_per_word).filter(v => v > 0.0005);
  const refs = { cost: paid.length ? Math.min(...paid) : 0, time: timed.length ? Math.min(...timed) : 0 };
  const methods = [...copy.order];
  const key = { best: m => -(byMethod[m]?.summary.exact_rate ?? -1), cheap: m => byMethod[m] ? byMethod[m].summary.per_thousand : Infinity, fast: m => byMethod[m] ? byMethod[m].summary.seconds_per_word : Infinity }[state.sort];
  methods.sort((a, b) => key(a) - key(b));
  const sorts = [['best', 'Best'], ['cheap', 'Cheapest'], ['fast', 'Fastest']].map(([id, l]) => `<button class="seg${state.sort === id ? ' on' : ''}" data-sort="${id}">${l}</button>`).join('');
  const head = `<div class="rank-head"><span class="segs sort">${sorts}</span><span>${esc(copy.board.cost)}</span><span>${esc(copy.board.time)}</span><span class="wide">${esc(copy.board.correct)}</span></div>`;
  $('rank').innerHTML = `${head}<div class="rank-scroll"><div class="rank-title">${esc(copy.board.title)}</div>${methods.map(m => rankRow(m, byMethod[m], refs)).join('')}</div>`;
}

function renderHow() {
  const info = copy.methods[state.method];
  if (!info) { $('how').innerHTML = `<div class="empty">${esc(copy.board.pick)}</div>`; return; }
  const absent = !inSet().some(r => r.method === state.method);
  const jumps = absent ? runs.filter(r => r.method === state.method).map(r => `<button class="pill tiny" data-goto="${esc(r.experiment)}" data-tip="${esc(copy.board.gotoTip)}">${esc(copy.sets[r.set])} · ${Math.round(r.summary.exact_rate * 100)}%</button>`).join('') : '';
  const note = absent ? `<div class="note">${esc(copy.board.notRunNote)}</div><div class="chips">${jumps}</div>` : '';
  $('how').innerHTML = `<h2>${esc(info.name)}</h2><p class="how-blurb">${esc(info.blurb)}</p>${note}<ol class="how-steps">${info.steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol><div class="how-label">${esc(copy.board.example)}</div><code class="example">${esc(info.example)}</code>`;
}

function fmt(spec, s) {
  const v = s[spec.key];
  if (v === undefined || v === null) return '–';
  if (spec.kind === 'pct') return Math.round(v * 100) + '%';
  if (spec.kind === 'usd') return '$' + v.toFixed(4);
  return fmtTime(v);
}

function renderHeadline() {
  const s = data.summary;
  const toggle = `<button class="pill tiny" data-act="details">${state.detailsOpen ? copy.headline.less : copy.headline.details} ${state.detailsOpen ? '▾' : '▸'}</button>`;
  const right = data.partial ? s.exact : data.words.filter(w => w.exact).length;
  const part = data.partial ? ` · ${copy.headline.partial}` : '';
  $('headline').innerHTML = `<span class="big">${Math.round(s.exact_rate * 100)}%</span><span class="sub">${copy.headline.exact} · ${right.toLocaleString()} ${copy.headline.of} ${s.words.toLocaleString()} ${copy.headline.words}${part}</span>${toggle}`;
  $('details').hidden = !state.detailsOpen;
  $('details').innerHTML = copy.details.filter(d => s[d.key] !== undefined).map(d => `<div class="detail" data-tip="${esc(d.tip)}"><b>${fmt(d, s)}</b><span>${esc(d.label)}</span></div>`).join('');
}

function renderFilters() {
  const tags = [...new Set(data.words.flatMap(w => w.tags))].sort();
  const toggle = `<button class="pill tiny" data-act="tags">${copy.filters.tags} ${state.tagsOpen ? '▾' : '▸'}</button>`;
  const chips = state.tagsOpen ? tags.map(t => `<button class="pill tiny${state.tags.has(t) ? ' on' : ''}" data-tag="${esc(t)}">${esc(t)}</button>`).join('') : '';
  const segs = seg('all', copy.filters.all, '', state.filter === 'all') + seg('wrong', copy.filters.wrong, copy.filters.wrongTip, state.filter === 'wrong');
  $('filters').innerHTML = `<div class="segs" id="filter-segs">${segs}</div>${toggle}${chips}`;
}

const visible = () => data.words.filter(w => (state.filter !== 'wrong' || !w.exact) && (!state.tags.size || w.tags.some(t => state.tags.has(t))));

function card(w) {
  const mask = lcsMask(w.pred, w.truth);
  const sel = w.id === state.selected ? ' sel' : '';
  const sense = w.sense ? `<div class="pickline hint" data-tip="${esc(w.sense)}">${esc(w.sense)}</div>` : '';
  return `<button class="card${sel}" data-word="${esc(w.id)}"><div class="card-head"><span class="card-word">${esc(w.word)}</span><span class="mark ${w.exact ? 'ok' : 'no'}">${w.exact ? '✓' : '✗'}</span></div>${sense}${phoneRow(w.pred, state.notation, mask)}</button>`;
}

function renderPanel() {
  const w = data.words.find(x => x.id === state.selected);
  if (!w) { $('panel').innerHTML = `<div class="empty">${esc(copy.empty)}</div>`; return; }
  const mask = lcsMask(w.pred, w.truth);
  const sense = w.sense ? `<div class="chips"><span class="chip sense">${esc(w.sense)}</span></div>` : '';
  const truths = w.truth.map(t => `<div class="lane"><div class="lane-label">${esc(copy.lanes.truth)}</div>${phoneRow(t, state.notation, null, true)}</div>`).join('');
  const cands = (w.candidates || []).length ? `<div class="lane"><div class="lane-label">${esc(copy.lanes.candidates)}</div>${candidateRows(w, state.notation, w.truth)}</div>` : '';
  const flag = w.flag ? `<div class="chips"><span class="chip ${w.flag === 'agree' ? 'agree' : 'differs'}">${w.flag === 'agree' ? 'second dictionary agrees' : w.flag === 'unchecked' ? 'not in the second dictionary' : 'second dictionary differs'}</span></div>` : '';
  $('panel').innerHTML = `<div class="p-head"><span class="p-word">${esc(w.word)}</span></div>${sense}${flag}<div class="lane"><div class="lane-label">${esc(copy.lanes.pred)}</div>${phoneRow(w.pred, state.notation, mask, true)}</div>${truths}${cands}`;
}

function setCaption(id) {
  const run = runs.find(r => r.set === id);
  return run ? `${(run.total_words || run.summary.words).toLocaleString()} words` : '';
}

function pickSet(id) {
  const pool = runs.filter(r => r.set === id && r.method !== 'lookup');
  state.set = id;
  open([...(pool.length ? pool : runs.filter(r => r.set === id))].sort((a, b) => b.summary.exact_rate - a.summary.exact_rate)[0].experiment);
}

function renderSets() {
  const ids = Object.keys(copy.sets).filter(id => runs.some(r => r.set === id));
  const items = ids.map(id => ({ id, label: copy.sets[id], caption: setCaption(id), tip: copy.setTips[id] }));
  mountShell({ groups: [{ id: 'sets', label: 'Test sets', items }], active: state.set, onSelect: pickSet });
  $('title').textContent = copy.sets[state.set] || '';
  $('subtitle').textContent = copy.setTips[state.set] || '';
  $('notation').innerHTML = copy.notations.map(n => seg(n.id, n.label, n.tip, n.id === state.notation)).join('');
}

function renderAll() { renderSets(); renderRank(); renderHow(); renderHeadline(); renderFilters(); $('grid').innerHTML = visible().map(card).join(''); renderPanel(); }

function open(name) {
  data = all[name];
  state.run = name; state.method = data.method; state.set = data.set;
  state.selected = data.words.some(w => w.id === state.selected) ? state.selected : null;
  state.filter = 'all';
  renderAll();
}

function defaultRun() {
  const here = inSet();
  const pool = here.filter(r => r.method !== 'lookup');
  return [...(pool.length ? pool : here)].sort((a, b) => b.summary.exact_rate - a.summary.exact_rate)[0];
}

function onClick(event) {
  const t = event.target.closest('button');
  if (!t) return;
  if (t.dataset.goto) return open(t.dataset.goto);
  if (t.dataset.sort) { state.sort = t.dataset.sort; return renderRank(); }
  if (t.dataset.method) { const run = inSet().find(r => r.method === t.dataset.method); if (run) return open(run.experiment); state.method = t.dataset.method; renderRank(); return renderHow(); }
  if (t.dataset.word) { state.selected = t.dataset.word; $('grid').innerHTML = visible().map(card).join(''); return renderPanel(); }
  if (t.dataset.tag) { state.tags.has(t.dataset.tag) ? state.tags.delete(t.dataset.tag) : state.tags.add(t.dataset.tag); renderFilters(); $('grid').innerHTML = visible().map(card).join(''); return; }
  if (t.dataset.act === 'details') { state.detailsOpen = !state.detailsOpen; return renderHeadline(); }
  if (t.dataset.act === 'tags') { state.tagsOpen = !state.tagsOpen; return renderFilters(); }
  if (t.closest('#notation')) { state.notation = t.dataset.id; remember(); return renderAll(); }
  if (t.closest('#filter-segs')) { state.filter = t.dataset.id; renderFilters(); $('grid').innerHTML = visible().map(card).join(''); }
}

let ready = false;

export async function load() {
  if (ready) return;
  copy = await (await fetch('pron-copy.json')).json();
  await loadNotation();
  runs = await (await fetch('/api/results/pron')).json();
  (await Promise.all(runs.map(r => fetch(`../results/pron/${r.file}`).then(x => x.json())))).forEach(d => { all[d.experiment] = d; });
  ready = true;
}

export function mount(options = {}) {
  restore(!options.preload);
  const wanted = runs.find(r => r.experiment === state.run);
  if (wanted) state.set = wanted.set; else state.set = state.set && runs.some(r => r.set === state.set) ? state.set : Object.keys(copy.sets).find(id => runs.some(r => r.set === id));
  open((wanted || defaultRun()).experiment);
  if (state.method && !runs.some(r => r.method === state.method && r.set === state.set)) { renderRank(); renderHow(); }
}

export function deactivate() {
  document.removeEventListener('click', onClick);
}

export function activate() {
  deactivate();
  document.addEventListener('click', onClick);
  renderSets();
}
