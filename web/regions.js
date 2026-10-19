import { loadNotation } from './notation.js';
import { esc } from './units.js';
import { phoneRow, lcsMask } from './pron-view.js';
import './tips.js';
import { mountShell } from './shell.js';

const state = { notation: 'plain', method: null };
let copy = {};
let data = {};
const $ = id => document.getElementById(id);

const pct = v => Math.round(v * 100) + '%';
const fmtTime = v => (v < 0.001 ? (v * 1e6).toFixed(0) + ' µs' : v < 0.01 ? (v * 1000).toFixed(1) + ' ms' : (v * 1000).toFixed(0) + ' ms');

function renderRank() {
  const rows = data.methods.map((m, i) => {
    const on = m.name === state.method ? ' on' : '';
    return `<button class="rank-row${on}" data-method="${esc(m.name)}"><span class="badge">${m.reference ? '·' : 'ABCDE'[i]}</span><span class="rank-text"><b>${esc(m.name)}</b></span><span class="stat"><b>free</b></span><span class="stat"><b>${fmtTime(m.seconds_per_word)}</b></span><span class="rank-bar"><i style="--c:${Math.round(m.match * 100)}%"></i></span><em>${pct(m.match)}</em></button>`;
  }).join('');
  const heads = copy.methodHeads;
  $('rank').innerHTML = `<div class="rank-head"><span class="segs sort" style="grid-column:1/3">${esc(copy.methodsTitle)}</span><span>${esc(heads.cost)}</span><span>${esc(heads.time)}</span><span class="wide">${esc(heads.match)}</span></div><div class="rank-scroll">${rows}</div>`;
}

function renderHow() {
  const steps = copy.howByMethod[state.method] || [];
  $('how').innerHTML = `<h2>${esc(state.method || '')}</h2><p class="how-blurb">${esc(copy.methodsNote)}</p><ol class="how-steps">${steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol>`;
}

function renderDiffs() {
  const rows = Object.entries(data.differences).map(([name, v]) => `<div class="barrow"><span>${esc(name)}</span><span class="track"><i style="--c:${Math.round(v * 100)}%"></i></span><b>${v < 0.01 ? '<1%' : pct(v)}</b></div>`).join('');
  $('diffs').innerHTML = rows;
}

function renderFacts() {
  $('facts').innerHTML = copy.facts.map(([title, what, status]) => `<div class="region-grid fact"><span class="region-word">${esc(title)}<small>${esc(what)}</small></span><span>${esc(status)}</span></div>`).join('');
}

function cell(phones, mode, reference) {
  const mask = reference ? lcsMask(phones.map(p => p.replace(/\d/g, '')), [reference.map(p => p.replace(/\d/g, ''))]) : null;
  return phoneRow(phones, mode, mask);
}

function row(w) {
  const wiki = w.uk_wikipron.length ? w.uk_wikipron.map(v => cell(v, state.notation, w.us)).join('<div style="height:4px"></div>') : '<span class="chip">no entry</span>';
  const match = w.uk_matches === null ? '' : `<span class="chip ${w.uk_matches ? 'agree' : 'differs'}" data-tip="${esc(copy.methodsNote)}">${w.uk_matches ? esc(copy.matches) : esc(copy.noMatch)}</span>`;
  const units = w.same_units === null ? '' : `<span class="chip ${w.same_units ? 'agree' : 'differs'}">${w.same_units ? esc(copy.unitsSame) : esc(copy.unitsDiffer)}</span>`;
  const canada = `${cell(w.canada, state.notation, w.us)}${w.canada_changed ? `<span class="chip" data-tip="${esc(copy.canadaTip)}">${esc(copy.changed)}</span>` : ''}`;
  return `<div class="region-grid"><span class="region-word">${esc(w.word)}<small>${units}</small></span><div>${phoneRow(w.us, state.notation, null)}</div><div>${cell(w.uk_rules, state.notation, w.us)}${match}</div><div>${wiki}</div><div>${canada}</div></div>`;
}

function renderGrid() {
  const heads = copy.heads.map(h => `<span>${esc(h)}</span>`).join('');
  $('grid').innerHTML = `<div class="region-grid head">${heads}</div>${data.words.map(row).join('')}`;
}

function renderAll() {
  $('notation').innerHTML = copy.notations.map(n => `<button class="seg${n.id === state.notation ? ' on' : ''}" data-id="${n.id}" data-tip="${esc(n.tip)}">${esc(n.label)}</button>`).join('');
  renderRank(); renderHow(); renderGrid();
}

function onClick(event) {
  const t = event.target.closest('button');
  if (!t) return;
  if (t.dataset.method) { state.method = t.dataset.method; renderRank(); return renderHow(); }
  if (t.closest('#notation')) { state.notation = t.dataset.id; renderAll(); }
}

let ready = false;

export async function load() {
  if (ready) return;
  copy = await (await fetch('regions-copy.json')).json();
  await loadNotation();
  data = await (await fetch('../results/regions/regions.json')).json();
  state.method = data.methods[data.methods.length - 2].name;
  ready = true;
}

export function mount() {
  $('title').textContent = copy.title;
  $('subtitle').textContent = copy.intro;
  $('diff-title').textContent = copy.diffTitle;
  $('diff-title').dataset.tip = copy.diffTip;
  $('facts-title').textContent = copy.factsTitle;
  $('grid-title').textContent = copy.gridTitle;
  $('alignment-note').textContent = copy.alignmentText;
  $('canada-note').textContent = data.canada_note;
  renderDiffs(); renderFacts(); renderAll();
}

export function deactivate() {
  document.removeEventListener('click', onClick);
}

export function activate() {
  deactivate();
  document.addEventListener('click', onClick);
  mountShell({ groups: [], active: null });
}
