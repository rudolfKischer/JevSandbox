import { loadNotation } from './notation.js';
import { wordStatus } from './diff.js';
import { miniHtml, esc } from './units.js';
import { panelHtml } from './panel.js';
import { pickLine, taskPanel } from './tasks.js';
import { groupRuns, renderRank, renderHow, variantLabel, metricOf, setOf, pctText } from './board.js';
import { findDoubts } from './consensus.js';
import { slotHtml, fillSources, eligible } from './sourcelane.js';
import { mountShell } from './shell.js';
import './tips.js';

const KEY = 'alignment-lab';
const state = { notation: 'plain', run: null, method: null, other: null, filter: 'all', tags: new Set(), selected: null, why: false, tagsOpen: false, detailsOpen: false, doubts: {}, sort: 'best', historyOpen: false, nettalk: {}, judged: {}, set: null, kind: 'all', unlabeled: false, partial: false };
let copy = {};
let runs = [];
let all = {};
let data = {};

const $ = id => document.getElementById(id);

function remember() {
  try { localStorage.setItem(KEY, JSON.stringify({ notation: state.notation, why: state.why })); } catch (e) {}
}

function restore(useParams = true) {
  try { Object.assign(state, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) {}
  if (!useParams) return;
  const params = new URLSearchParams(location.search);
  if (params.get('run')) state.run = params.get('run');
  if (params.get('word')) state.selected = params.get('word');
  window.forcedMethod = params.get('method');
}

const seg = (id, label, tip, on) => `<button class="seg${on ? ' on' : ''}" data-id="${id}" data-tip="${esc(tip)}">${esc(label)}</button>`;

function renderNotation() {
  $('notation').innerHTML = copy.notations.map(n => seg(n.id, n.label, n.tip, n.id === state.notation)).join('');
}

const isHistory = id => copy.setGroups.history.includes(id);

function setIds(group) {
  return copy.setGroups[group].filter(id => runs.some(run => setOf(run) === id));
}

const allowedMethods = set => (isHistory(set) ? null : new Set([...copy.currentMethods, ...copy.referenceMethods]));

const order = method => { const at = copy.currentMethods.indexOf(method); return at < 0 ? 99 : at; };

const groupsHere = () => groupRuns(runs, state.set, allowedMethods(state.set)).sort((a, b) => order(a.method) - order(b.method));

function runsInSet() {
  const allowed = allowedMethods(state.set);
  return runs.filter(run => setOf(run) === state.set && (!allowed || allowed.has(run.method)));
}

function setRun(id) {
  const here = runs.filter(run => setOf(run) === id && (!allowedMethods(id) || allowedMethods(id).has(run.method)));
  return here.find(run => run.method === 'r') || here[0];
}

function setCaption(id) {
  const run = setRun(id);
  if (!run) return '';
  if (id === 'tasks') return `${runs.filter(r => setOf(r) === id).length} tests`;
  const words = `${run.summary.scored.toLocaleString()} words`;
  if (isHistory(id)) return `${words} \u00b7 ${new Set(runs.filter(r => setOf(r) === id).map(r => r.method)).size} methods`;
  return `${words} \u00b7 ${pctText(metricOf(run))}${run.summary.exact_rate === null ? ' agree' : ''}`;
}

function navItem(id) {
  return { id, label: copy.setNav[id], caption: setCaption(id), tip: copy.setTips[id] };
}

function pickSet(id) {
  state.set = id;
  openRun(defaultRun().experiment);
}

function renderSets() {
  const groups = [
    { id: 'current', label: copy.navGroups.current, items: setIds('main').map(navItem) },
    { id: 'history', label: copy.navGroups.history, collapsible: true, muted: true, note: copy.navGroups.historyNote, items: setIds('history').map(navItem) },
  ];
  mountShell({ groups, active: state.set, onSelect: pickSet });
  $('title').textContent = copy.setNav[state.set] || '';
  $('subtitle').textContent = copy.setTips[state.set] || '';
  $('banner').hidden = !isHistory(state.set);
  $('banner').textContent = copy.board.historyNote;
}

function currentGroup() {
  return groupsHere().find(group => group.method === state.method);
}

function renderBoard() {
  renderRank($('rank'), groupsHere(), state, copy);
  renderHow($('how'), currentGroup(), state, copy);
}

function formatDetail(spec, summary) {
  const value = spec.key === 'seconds_per_word' ? summary.timing?.seconds_per_word : summary[spec.key];
  if (value === undefined || value === null || (spec.key === 'auc' && !value)) return '–';
  if (spec.kind === 'pct') return Math.round(value * 100) + '%';
  if (spec.kind === 'usd') return '$' + value.toFixed(4);
  if (spec.kind === 'int') return value.toLocaleString();
  if (spec.kind === 'sec') return value < 0.01 ? (value * 1000).toFixed(1) + ' ms' : value.toFixed(2) + ' s';
  return value.toFixed(2);
}

function judgedEstimate() {
  if (data.gold !== 'large' || !Object.keys(state.judged).length) return null;
  const rows = data.words.filter(row => state.judged[row.word] && (row.category_pred || 'word') === 'word');
  if (!rows.length) return null;
  const points = rows.reduce((sum, row) => sum + ({ ok: 1, doubtful: 0.5, wrong: 0 }[state.judged[row.word].verdict]), 0);
  return Math.round(points / rows.length * 100);
}

function renderHeadline() {
  const s = data.summary;
  const h = copy.headline;
  const toggle = `<button class="pill tiny" data-act="details">${state.detailsOpen ? h.less : h.details} ${state.detailsOpen ? '▾' : '▸'}</button>`;
  if (data.partial) {
    const kept = data.words.length.toLocaleString();
    const total = data.total_words.toLocaleString();
    $('headline').innerHTML = `<span class="big">${Math.round((s.nettalk_agree || 0) * 100)}%</span><span class="sub">${h.nettalkAgrees} · ${total} ${h.words} · $${s.cost_usd.toFixed(2)} ${h.costWord} · ${s.flagged.toLocaleString()} ${h.flaggedN} · ${h.showing} ${kept}. ${h.partialNote}</span>${toggle}`;
  } else if (s.exact_rate === null) {
    const est = judgedEstimate();
    const agree = s.nettalk_agree !== undefined ? ` · ${Math.round(s.nettalk_agree * 100)}% ${h.nettalkAgrees}` : '';
    const sure = `${Math.round((s.confident_rate || 0) * 100)}% ${h.confident}`;
    if (est) $('headline').innerHTML = `<span class="big" data-tip="${esc(h.judged)}">≈${est}%</span><span class="sub">${h.estimated} (${h.judged}) · ${sure} · ${s.scored} ${h.words}${agree}</span>${toggle}`;
    else $('headline').innerHTML = `<span class="big">${Math.round((s.confident_rate || 0) * 100)}%</span><span class="sub">${h.confident} · ${s.scored} ${h.words}${agree}</span>${toggle}`;
  } else {
    const percent = s.scored ? pctText(s.exact_rate) : '–';
    const judged = s.wrong !== undefined ? ` · ${s.scored - s.exact} ${h.notRight} (${s.doubtful} ${h.doubtfulN} + ${s.wrong} ${h.wrongN}${s.unread ? ` + ${s.unread} ${h.unreadN}` : ''})` : '';
    const note = copy.setNote[state.set] ? ` · ${copy.setNote[state.set]}` : '';
    $('headline').innerHTML = `<span class="big">${percent}</span><span class="sub">${h.correct} · ${s.exact} ${h.of} ${s.scored} ${h.words}${judged}${note}</span>${toggle}`;
  }
  $('details').hidden = !state.detailsOpen;
  $('details').innerHTML = copy.details.map(spec => `<div class="detail" data-tip="${esc(spec.tip)}"><b>${formatDetail(spec, s)}</b><span>${esc(spec.label)}</span></div>`).join('');
}

function allTags() {
  return [...new Set(data.words.flatMap(row => row.tags))].sort();
}

const kindOf = row => row.category_pred || row.category || 'word';

function kindList() {
  const present = new Set(data.words.map(kindOf));
  return ['all', 'word', 'initialism', 'abbreviation', 'mixed'].filter(k => k === 'all' || present.has(k));
}

const isJudged = () => data.words.some(row => row.judge);

const FILTER_TESTS = {
  all: () => true,
  wrong: (row, status) => status === 'no',
  notright: (row, status) => status !== 'ok' && status !== 'na',
  unsure: (row, status, below) => (row.judge ? ['doubtful', 'unread'].includes(row.judge.verdict) : row.posterior !== undefined && row.posterior < below),
  nettalk: row => row.nettalk_ok === false,
  baseline: row => row.baseline_same === false,
  doubt: row => Boolean(state.doubts[row.id]),
};

function passes(id, row) {
  return FILTER_TESTS[id](row, wordStatus(row, copy.unsureBelow), copy.unsureBelow);
}

function filterIds() {
  if (state.unlabeled) return data.partial ? ['all', 'unsure', 'nettalk', 'baseline'] : ['all', 'unsure', 'nettalk'];
  return isJudged() ? ['all', 'notright', 'wrong', 'unsure'] : ['all', 'wrong', 'unsure'];
}

function filterSpec(id) {
  const f = copy.filters;
  if (isJudged() && id === 'wrong') return f.wrongJudged;
  if (isJudged() && id === 'unsure') return f.doubtful;
  return f[id];
}

function filterSeg(id) {
  const spec = filterSpec(id);
  const count = id === 'all' || data.partial ? '' : ` ${data.words.filter(row => passes(id, row)).length}`;
  return seg(id, spec.label + count, spec.tip, state.filter === id);
}

function renderFilters() {
  const f = copy.filters;
  const hasDoubts = data.kind !== 'task' && !state.unlabeled && Object.keys(state.doubts).length;
  const segs = filterIds().map(filterSeg).join('') + (hasDoubts ? seg('doubt', copy.doubt.label, copy.doubt.tip, state.filter === 'doubt') : '');
  const toggle = `<button class="pill tiny" data-act="tags" data-tip="${esc(f.tags.tip)}">${f.tags.label} ${state.tagsOpen ? '\u25be' : '\u25b8'}</button>`;
  const kinds = kindList();
  const kindSegs = kinds.length > 2 ? `<div class="segs" id="kind-segs">${kinds.map(k => seg(k, copy.kinds[k], copy.kindTips[k], state.kind === k)).join('')}</div>` : '';
  const tags = state.tagsOpen ? allTags().map(tag => `<button class="pill tiny${state.tags.has(tag) ? ' on' : ''}" data-tag="${esc(tag)}">${esc(tag)}</button>`).join('') : '';
  $('filters').innerHTML = `<div class="segs" id="filter-segs">${segs}</div>${kindSegs}${toggle}${tags}`;
}

function visible() {
  return data.words.filter(row => {
    if (!passes(state.filter, row)) return false;
    if (state.kind !== 'all' && kindOf(row) !== state.kind) return false;
    return !state.tags.size || row.tags.some(tag => state.tags.has(tag));
  });
}

function card(row) {
  const status = wordStatus(row, copy.unsureBelow);
  const sel = row.id === state.selected ? ' sel' : '';
  const flag = state.doubts[row.id] && data.kind !== 'task' ? `<span class="mark doubt" data-tip="${esc(copy.doubt.tip)}">⚑</span>` : '';
  const body = data.kind === 'task' ? pickLine(row, state, copy) : miniHtml(row, state, copy);
  return `<button class="card${sel}" data-word="${esc(row.id)}"><div class="card-head"><span class="card-word">${esc(row.word)}</span><span>${flag}<span class="mark ${status}">${copy.marks[status]}</span></span></div>${body}</button>`;
}

function renderPatterns() {
  const counts = {};
  data.words.forEach(row => { if (row.judge && row.judge.verdict !== 'ok' && row.judge.pattern) counts[row.judge.pattern] = (counts[row.judge.pattern] || 0) + 1; });
  const items = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  $('patterns').hidden = !items.length;
  $('patterns').innerHTML = items.length ? `<span class="how-label">${esc(copy.headline.patterns)}</span>` + items.map(([name, n]) => `<button class="pill tiny${state.tags.has(name) ? ' on' : ''}" data-tag="${esc(name)}">${esc(name)} · ${n}</button>`).join('') : '';
}

function renderGrid() {
  $('grid').innerHTML = visible().map(card).join('');
}

function peers() {
  return runs.filter(run => run.experiment !== state.run && run.kind === data.kind && run.gold === data.gold);
}

function renderPanel() {
  const row = data.words.find(item => item.id === state.selected);
  if (data.kind === 'task' && row) { $('panel').innerHTML = taskPanel(row, state, copy); return; }
  const other = state.other ? all[state.other]?.words.find(item => item.id === state.selected) : null;
  const options = peers().map(run => `<option value="${esc(run.experiment)}"${run.experiment === state.other ? ' selected' : ''}>${esc((copy.methods[run.method]?.name || run.method) + ' · ' + variantLabel(run, copy))}</option>`).join('');
  const compare = row ? `<select class="cmp" id="compare" data-tip="${esc(copy.compare.tip)}"><option value="">${copy.compare.label}: ${copy.compare.none}</option>${options}</select>` : '';
  $('panel').innerHTML = panelHtml(row, other, state, copy, compare) + (eligible(row) && data.kind !== 'task' ? slotHtml(copy) : '');
  if (eligible(row) && data.kind !== 'task') fillSources(row, state, copy);
}

function renderAll() {
  renderSets();
  $('draft').hidden = !data.words.some(row => row.gold && row.gold.length);
  $('draft').textContent = copy.draft.label;
  $('draft').dataset.tip = copy.draft.tip;
  renderNotation(); renderBoard(); renderHeadline(); renderFilters(); renderPatterns(); renderGrid(); renderPanel();
}

function openRun(name) {
  data = all[name];
  data.summary.live = data.live;
  state.run = name;
  state.set = setOf(data);
  state.history = isHistory(state.set);
  state.unlabeled = data.summary.exact_rate === null;
  state.partial = Boolean(data.partial);
  if (!filterIds().includes(state.filter) && state.filter !== 'doubt') state.filter = 'all';
  state.kind = 'all';
  state.method = data.method;
  if (state.filter === 'doubt' && data.kind === 'task') state.filter = 'all';
  state.selected = data.words.some(item => item.id === state.selected) ? state.selected : null;
  if (state.other && !peers().some(run => run.experiment === state.other)) state.other = null;
  renderAll();
}

function defaultRun() {
  state.set = state.set && runs.some(r => setOf(r) === state.set) ? state.set : setIds('main')[0];
  const inSet = runsInSet();
  const routers = inSet.filter(run => run.method === 'r');
  const pool = routers.length ? routers : inSet;
  return [...pool].sort((a, b) => metricOf(b) - metricOf(a))[0];
}

function pickMethod(method) {
  const group = groupsHere().find(x => x.method === method);
  if (!group || !group.best) return;
  const current = group.runs.find(run => run.experiment === state.run);
  return openRun((current || group.best).experiment);
}

function onClick(event) {
  const t = event.target.closest('button');
  if (!t) return;
  if (t.closest('#kind-segs')) { state.kind = t.dataset.id; renderFilters(); return renderGrid(); }
  if (t.dataset.sort) { state.sort = t.dataset.sort; return renderBoard(); }
  if (t.dataset.run) return openRun(t.dataset.run);
  if (t.dataset.method) return pickMethod(t.dataset.method);
  if (t.dataset.goto) return openRun(t.dataset.goto);
  if (t.dataset.word) { state.selected = t.dataset.word; renderGrid(); return renderPanel(); }
  if (t.dataset.tag) { state.tags.has(t.dataset.tag) ? state.tags.delete(t.dataset.tag) : state.tags.add(t.dataset.tag); renderFilters(); renderPatterns(); return renderGrid(); }
  if (t.dataset.act === 'why') { state.why = !state.why; remember(); return renderPanel(); }
  if (t.dataset.act === 'details') { state.detailsOpen = !state.detailsOpen; return renderHeadline(); }
  if (t.dataset.act === 'tags') { state.tagsOpen = !state.tagsOpen; return renderFilters(); }
  if (t.closest('#notation')) { state.notation = t.dataset.id; remember(); return renderAll(); }
  if (t.closest('#filter-segs')) { state.filter = t.dataset.id; renderFilters(); renderGrid(); }
}

function onChange(event) {
  if (event.target.id !== 'compare') return;
  state.other = event.target.value || null;
  renderPanel();
}

let ready = false;

export async function load() {
  if (ready) return;
  copy = await (await fetch('copy.json')).json();
  await loadNotation();
  runs = await (await fetch('/api/results')).json();
  const loaded = await Promise.all(runs.map(run => fetch(`../results/${run.file}`).then(r => r.json())));
  loaded.forEach(item => { all[item.experiment] = item; });
  state.doubts = findDoubts(all);
  state.judged = await fetch('../data/samples/large-judged.json').then(r => (r.ok ? r.json() : { words: {} })).then(d => d.words).catch(() => ({}));
  state.nettalk = await fetch('../data/external/nettalk-compare.json').then(r => (r.ok ? r.json() : { words: {} })).then(d => d.words).catch(() => ({}));
  ready = true;
}

export function mount(options = {}) {
  restore(!options.preload);
  const first = runs.find(run => run.experiment === state.run) || defaultRun();
  if (first) openRun(first.experiment);
  if (window.forcedMethod && !options.preload) { state.method = window.forcedMethod; renderBoard(); }
}

export function deactivate() {
  document.removeEventListener('click', onClick);
  document.removeEventListener('change', onChange);
}

export function activate() {
  deactivate();
  document.addEventListener('click', onClick);
  document.addEventListener('change', onChange);
  renderSets();
}
