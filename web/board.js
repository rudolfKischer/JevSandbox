import { esc } from './units.js';

const PLAIN = 'plain';

export const pctText = v => (v >= 0.98 && v < 1 ? (v * 100).toFixed(1) : String(Math.round(v * 100))) + '%';

export const metricOf = run => run.summary.exact_rate ?? (run.summary.flagged !== undefined ? run.summary.nettalk_agree : run.summary.confident_rate) ?? 0;

export function methodOf(run) {
  return run.method;
}

export const setOf = run => (run.kind === 'task' ? 'tasks' : run.gold);

export function groupRuns(runs, set, allowed = null) {
  const groups = {};
  runs.forEach(run => {
    if (allowed && !allowed.has(run.method)) return;
    const group = groups[run.method] = groups[run.method] || { method: run.method, kind: run.kind || 'alignment', all: [] };
    group.all.push(run);
  });
  return Object.values(groups)
    .filter(group => (set === 'tasks') === (group.kind === 'task') && group.all.some(run => setOf(run) === set))
    .map(group => {
      const here = group.all.filter(run => setOf(run) === set);
      const best = here.length ? here.reduce((top, run) => (metricOf(run) > metricOf(top) ? run : top), here[0]) : null;
      return { ...group, runs: here, best, elsewhere: group.all.filter(run => setOf(run) !== set) };
    });
}

export function variantParts(run, copy) {
  const config = run.config || {};
  const parts = [];
  if (config.scheme === 'grapheme') parts.push('graphemes');
  if (config.local_model) parts.push(config.local_model.includes('1b') ? 'local1b' : 'local3b');
  if (config.catalog_in_state) parts.push('catalog');
  if (config.examples) parts.push('examples');
  if (config.rules === false) parts.push('norules');
  return parts.length && !(parts.length === 1 && parts[0] === 'graphemes') ? parts : [...parts, PLAIN];
}

export function variantLabel(run, copy) {
  return variantParts(run, copy).map(part => copy.variants[part]).join(' ');
}

function badge(group) {
  if (group.method === 'baseline') return '·';
  return group.kind === 'task' ? '?' : group.method.toUpperCase();
}

const costOf = group => group.best?.summary.per_thousand || 0;
const timeOf = group => group.best?.summary.timing?.seconds_per_word;
const usesModel = group => (group.best?.summary.timing?.requests_per_word || 0) > 0;

function references(groups) {
  const paid = groups.map(costOf).filter(value => value > 0);
  const timed = groups.filter(usesModel).map(timeOf).filter(value => value > 0);
  return { cost: paid.length ? Math.min(...paid) : 0, time: timed.length ? Math.min(...timed) : 0 };
}

export function sortGroups(groups, order) {
  const key = { best: g => -(g.method === 'e' ? 0 : metricOf(g.best)), cheap: g => costOf(g), fast: g => timeOf(g) ?? Infinity }[order];
  const present = groups.filter(g => g.best);
  const absent = groups.filter(g => !g.best);
  return [...present].sort((a, b) => key(a) - key(b) || metricOf(b.best) - metricOf(a.best)).concat(absent);
}

function fmtMoney(value) {
  return value < 0.01 ? '$' + value.toFixed(4) : '$' + value.toFixed(3);
}

function costCell(group, ref, copy) {
  const value = costOf(group);
  if (!value) return `<span class="stat" data-tip="${esc(copy.board.free)}"><b>${esc(usesModel(group) ? copy.board.free : copy.board.noModel)}</b></span>`;
  const times = ref.cost ? value / ref.cost : 1;
  const tip = `${fmtMoney(value)} per 1,000 words. ${times > 1 ? `+${fmtMoney(value - ref.cost)} more than the cheapest paid method (${times.toFixed(1)}×).` : 'This is the cheapest paid method.'}`;
  return `<span class="stat" data-tip="${esc(tip)}"><b>${fmtMoney(value)}</b><small>×${times.toFixed(times < 10 ? 1 : 0)}</small></span>`;
}

function timeCell(group, ref, copy) {
  const value = timeOf(group);
  if (value === undefined) return '<span class="stat"><b>–</b></span>';
  const text = value < 0.01 ? `${(value * 1000).toFixed(1)} ms` : `${value.toFixed(2)} s`;
  if (!usesModel(group)) return `<span class="stat" data-tip="${esc(text + ' per word. Runs on code alone.')}"><b>${esc(text)}</b></span>`;
  const times = ref.time ? value / ref.time : 1;
  const tip = `${text} per word. ${times > 1.05 ? `+${(value - ref.time).toFixed(2)} s more than the fastest model method (${times.toFixed(1)}×).` : 'This is the fastest model method.'}`;
  return `<span class="stat" data-tip="${esc(tip)}"><b>${esc(text)}</b><small>×${times.toFixed(times < 10 ? 1 : 0)}</small></span>`;
}

function rankRow(group, state, copy, ref) {
  const info = copy.methods[group.method] || { name: group.method, blurb: '' };
  const audit = info.metric === 'auc';
  const percent = Math.round((audit ? group.best.summary.auc : metricOf(group.best)) * 100);
  const empty = !audit && metricOf(group.best) === 0;
  const shown = empty ? '–' : audit ? `AUC .${percent}` : pctText(metricOf(group.best));
  const on = group.method === state.method ? ' on' : '';
  const versions = group.runs.length > 1 ? ` <span class="count">· ${group.runs.length} ${copy.board.versions}</span>` : '';
  return `<button class="rank-row${on}" data-method="${esc(group.method)}"><span class="badge">${badge(group)}</span><span class="rank-text"><b>${esc(info.name)}${versions}</b><small>${esc(info.blurb)}</small></span>${costCell(group, ref, copy)}${timeCell(group, ref, copy)}<span class="rank-bar"><i style="--c:${percent}%"></i></span><em data-tip="${group.best.summary.scored} words">${shown}</em></button>`;
}

const headLabel = (state, copy) => (state.partial ? copy.headline.nettalkAgrees : state.unlabeled ? copy.headline.confident : copy.board.correctHead);

function headRow(state, copy) {
  const tips = copy.boardTips;
  const sorts = [['best', copy.board.sortBest], ['cheap', copy.board.sortCheap], ['fast', copy.board.sortFast]];
  const segs = sorts.map(([id, label]) => `<button class="seg${state.sort === id ? ' on' : ''}" data-sort="${id}">${esc(label)}</button>`).join('');
  return `<div class="rank-head"><span class="segs sort">${segs}</span><span data-tip="${esc(tips.costHead)}">${esc(copy.board.costHead)}</span><span data-tip="${esc(tips.timeHead)}">${esc(copy.board.timeHead)}</span><span class="wide" data-tip="${esc(tips.correctHead)}">${esc(headLabel(state, copy))}</span></div>`;
}

export function renderRank(el, groups, state, copy) {
  const ordered = sortGroups(groups, state.sort || 'best');
  const ref = references(groups.filter(g => g.best));
  const section = (title, list) => (list.length ? `<div class="rank-title">${esc(title)}</div>${list.map(g => rankRow(g, state, copy, ref)).join('')}` : '');
  const scroll = el.querySelector('.rank-scroll')?.scrollTop || 0;
  el.innerHTML = `${headRow(state, copy)}<div class="rank-scroll">${section(state.set === 'tasks' ? copy.board.tasks : state.history ? copy.board.earlier : copy.board.current, ordered)}</div>`;
  el.querySelector('.rank-scroll').scrollTop = scroll;
}

function variantChip(run, state, copy) {
  const on = run.experiment === state.run ? ' on' : '';
  const tip = variantParts(run, copy).map(part => copy.variantTips[part]).join('. ');
  return `<button class="pill tiny${on}" data-run="${esc(run.experiment)}" data-tip="${esc(tip)}">${esc(variantLabel(run, copy))} · ${Math.round(metricOf(run) * 100)}%</button>`;
}

export function renderHow(el, group, state, copy) {
  if (!group) { el.innerHTML = `<div class="empty">${esc(copy.board.pick)}</div>`; return; }
  const info = copy.methods[group.method] || { name: group.method, blurb: '', steps: [], example: '' };
  const steps = info.steps.map(step => `<li>${esc(step)}</li>`).join('');
  const example = info.example ? `<div class="how-label">${esc(copy.board.example)}</div><code class="example">${esc(info.example)}</code>` : '';
  const chips = group.runs.length > 1 ? `<div class="how-label">${esc(copy.board.variants)}</div><div class="chips">${group.runs.map(run => variantChip(run, state, copy)).join('')}</div>` : '';
  el.innerHTML = `<h2>${esc(info.name)}</h2><p class="how-blurb">${esc(info.blurb)}</p><ol class="how-steps">${steps}</ol>${example}${chips}`;
}
