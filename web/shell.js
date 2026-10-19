const PAGES = [
  ['index.html', 'Alignment', 'Letters to sounds'],
  ['pron.html', 'Pronunciation', 'Generating sounds'],
  ['sources.html', 'Sources', 'Other datasets'],
  ['regions.html', 'Regions', 'US, UK, Canada'],
];

const KEY = 'shell-open';
const side = () => document.getElementById('side');
const esc = text => String(text ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
let options = { groups: [], active: null, onSelect: () => {} };
let open = {};

function remember() {
  try { localStorage.setItem(KEY, JSON.stringify(open)); } catch (error) {}
}

function restore() {
  try { open = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (error) { open = {}; }
}

function pageLinks() {
  const here = location.pathname.split('/').pop() || 'index.html';
  return PAGES.map(([file, label, hint]) => `<a class="nav-item${file === here ? ' on' : ''}" href="${file}"><span class="nav-title">${label}</span><span class="nav-sub">${hint}</span></a>`).join('');
}

function itemHtml(item, active) {
  const sub = item.caption ? `<span class="nav-sub">${esc(item.caption)}</span>` : '';
  return `<button class="nav-item${item.id === active ? ' on' : ''}" data-set="${esc(item.id)}" data-tip="${esc(item.tip || '')}"><span class="nav-title">${esc(item.label)}</span>${sub}</button>`;
}

function groupHtml(group, active) {
  const holds = group.items.some(item => item.id === active);
  const expanded = !group.collapsible || open[group.id] === true || holds;
  const head = group.collapsible
    ? `<button class="nav-group" data-group="${esc(group.id)}"><span>${esc(group.label)}</span><span class="nav-count">${group.items.length}</span><span class="nav-chevron">${expanded ? '▾' : '▸'}</span></button>`
    : `<div class="nav-group static"><span>${esc(group.label)}</span></div>`;
  const note = expanded && group.note ? `<p class="nav-note">${esc(group.note)}</p>` : '';
  const items = expanded ? group.items.map(item => itemHtml(item, active)).join('') : '';
  return `<section class="nav-section${group.muted ? ' muted' : ''}">${head}${note}${items}</section>`;
}

function render() {
  const groups = options.groups.filter(group => group.items.length).map(group => groupHtml(group, options.active)).join('');
  side().innerHTML = `<a class="brand" href="index.html"><b>Word lab</b><span>Spelling and sound</span></a><nav class="nav-section"><div class="nav-group static"><span>Pages</span></div>${pageLinks()}</nav>${groups}`;
}

function onClick(event) {
  const target = event.target.closest('button');
  if (!target || !side().contains(target)) return;
  if (target.dataset.group) {
    open[target.dataset.group] = !(open[target.dataset.group] === true || options.groups.find(g => g.id === target.dataset.group).items.some(i => i.id === options.active));
    remember();
    render();
  } else if (target.dataset.set) {
    options.onSelect(target.dataset.set);
  }
}

export function mountShell(next) {
  options = { ...options, ...next };
  if (!side().dataset.ready) {
    restore();
    side().addEventListener('click', onClick);
    side().dataset.ready = '1';
  }
  render();
}
